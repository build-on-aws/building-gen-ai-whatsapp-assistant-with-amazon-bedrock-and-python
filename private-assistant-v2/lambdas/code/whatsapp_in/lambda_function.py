#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
##++++++ Amazon Lambda Function for processing WhatsApp incoming messages +++++
## Updated to Whatsapp API v14
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
import boto3
import decimal
import json
import os
from whatsapp import WhatsappService
from botocore.exceptions import ClientError


dynamodb = boto3.resource("dynamodb")
TABLE_NAME = os.environ.get("TABLE_NAME")
table = dynamodb.Table(TABLE_NAME)

TRANSCRIBE_PREFIX = os.environ.get("ENV_TRANSCRIBE_PREFIX")

LAMBDA_BEDROCK_AGENT = os.environ['ENV_LAMBDA_BEDROCK_AGENT'] 
lambda_client = boto3.client('lambda')
transcribe_client  = boto3.client('transcribe')

SUPPORTED_FILE_TYPES = ['text/csv','image/png','image/jpeg','application/pdf']

def process_record(record):
    sns = record.get("Sns", {})
    sns_message_str = sns.get("Message", "{}")
    sns_message = json.loads(sns_message_str, parse_float=decimal.Decimal)
    whatsapp_information = WhatsappService(sns_message)

    for message in whatsapp_information.messages:
        message_type = message.message.get("type")
        print("type: ",message_type)
        if message_type == "text":
            text = message.get_text()
            #message.text_reply(text.replace("/echo ", "")) 
            print("phone_number_id: ",message.phone_number_id)
            data = {
                'message': message.message,
                'phone_number_id' : message.phone_number_id,
                'metadata' : message.metadata
            }
            invoke_other_lambda(data,LAMBDA_BEDROCK_AGENT)

        else:
            media = message.get_media(message_type,download = True) # Check if there is media audio or image
            transcription = None
            if media.get("location"): # it's been downloaded
                print ("TRANSCRIBE IT")
                print(media.get("location"))
                s3Path = media.get("location")
                message.message["location"] = s3Path
                if message_type == "image":
                    data = {
                                'message': message.message,
                                'phone_number_id' : message.phone_number_id,
                                'metadata' : message.metadata,
                                'image_key': s3Path,
                            }
                    invoke_other_lambda(data,LAMBDA_BEDROCK_AGENT)
                elif message_type == "audio":
                    jobName = message.message["audio"]['id'] 
                    print(jobName) 
                    message.message["jobName"] = jobName
                    print("phone_number_id: ",message.phone_number_id)
                    fileId = s3Path.split("/")[-1].split(".")[-2]
                    mime_type = message.message["audio"]['mime_type']
                    codec = mime_type.split("/")[1].split(";")[0]
                    bucket_key_out = f"{TRANSCRIBE_PREFIX}/texto_{fileId}"
                    print("bucket_key: ",bucket_key_out)
                    start_job_transciptor (jobName,s3Path,bucket_key_out,codec)

        message.save(table)
        message.mark_as_read()
        message.reaction("👋")

def lambda_handler(event, context):
    print (event)
    records = event.get("Records", [])
    #print (f"processing {len(records)} records")
    for rec in records:
        process_record(rec)
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }

def invoke_other_lambda(data,lambda_name):
    print("message", data)
    try:       
        response = lambda_client.invoke(
            FunctionName = lambda_name,
            InvocationType = 'Event' ,#'RequestResponse', 
            Payload = json.dumps(data)
        )
        print(f'\nLambda response:{response}')
        return response
    except ClientError as e:
        err = e.response
        error = err
        print(err.get("Error", {}).get("Code"))
        return f"Un error invocando {lambda_name}"
    

def start_job_transciptor (jobName,s3Path_in,OutputKey,codec):
    print("MediaFileUri: ",s3Path_in)
    BucketName = s3Path_in.split('/')[2]
    print("Bucket Name: ", BucketName)
    response = transcribe_client.start_transcription_job(
            TranscriptionJobName=jobName,
            #LanguageCode='es-US',
            IdentifyLanguage=True,
            MediaFormat=codec,
            Media={
            'MediaFileUri': s3Path_in
            },
            OutputBucketName = BucketName,
            OutputKey=OutputKey 
            )
    TranscriptionJobName = response['TranscriptionJob']['TranscriptionJobName']
    job = transcribe_client.get_transcription_job(TranscriptionJobName=TranscriptionJobName)
    job_status = job['TranscriptionJob']['TranscriptionJobStatus']
    
    print("Processing....")
    print("Print job_status ....",job_status)
    print("TranscriptionJobName : {}".format(TranscriptionJobName))