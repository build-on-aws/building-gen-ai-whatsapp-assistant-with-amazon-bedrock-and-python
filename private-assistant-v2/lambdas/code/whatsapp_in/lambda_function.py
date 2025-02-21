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

import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)



dynamodb = boto3.resource("dynamodb")
lambda_client = boto3.client('lambda')
transcribe_client  = boto3.client('transcribe')

import os

class Config:
    TABLE_NAME = os.environ.get("TABLE_NAME")
    table = dynamodb.Table(TABLE_NAME)
    TRANSCRIBE_PREFIX = os.environ.get("ENV_TRANSCRIBE_PREFIX")
    LAMBDA_BEDROCK_AGENT = os.environ['ENV_LAMBDA_BEDROCK_AGENT']


def process_record(record):
    sns = record.get("Sns", {})
    sns_message = json.loads(sns.get("Message", "{}"), parse_float=decimal.Decimal)
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
            invoke_other_lambda(data,Config.LAMBDA_BEDROCK_AGENT)

        else:
            media = message.get_media(message_type,download = True) # Check if there is media audio or image
            transcription = None
            if media.get("location"): # it's been downloaded
                print ("TRANSCRIBE IT")
                print(media.get("location"))
                s3Path = media.get("location")
                message.message["location"] = s3Path
                if message_type == "image" or message_type == "video" or message_type == "document":
                    data = {
                                'message': message.message,
                                'phone_number_id' : message.phone_number_id,
                                'metadata' : message.metadata,
                                'image_key': s3Path,
                            }
                    invoke_other_lambda(data, Config.LAMBDA_BEDROCK_AGENT)

                elif message_type == "audio": 
                    jobName = message.message[message_type]['id'] 
                    print(jobName) 
                    message.message["jobName"] = jobName
                    fileId = s3Path.split("/")[-1].split(".")[-2]
                    mime_type = message.message[message_type]['mime_type']
                    codec = mime_type.split("/")[1].split(";")[0]
                    bucket_key_out = f"{Config.TRANSCRIBE_PREFIX}/{message_type}_{fileId}"
                    print("bucket_key: ",bucket_key_out)
                    start_job_transcriptor(jobName,s3Path,bucket_key_out,codec)
                else:
                    print("not supported message_type: ", message_type) 
                    message.text_reply(f"not supported message_type: {message_type}")

        message.save(Config.table)
        message.mark_as_read()
        message.reaction("👋")

def lambda_handler(event, context):
    try:
        records = event.get("Records", [])
        for rec in records:
            process_record(rec)
        return {
            'statusCode': 200,
            'body': json.dumps('Success')
        }
    except Exception as e:
        print(f"Error processing event: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps('Error processing request')
        }

def invoke_other_lambda(data, lambda_name):
    logger.info(f"Invoking lambda {lambda_name} with data: {data}")
    try:       
        response = lambda_client.invoke(
            FunctionName=lambda_name,
            InvocationType='Event',
            Payload=json.dumps(data)
        )
        # amazonq-ignore-next-line
        logger.info(f"Lambda response: {response}")
        return response
    except ClientError as e:
        logger.error(f"Error invoking lambda {lambda_name}: {str(e)}")
        raise

def start_job_transcriptor(job_name, s3_path_in, output_key, codec):
    try:
        bucket_name = s3_path_in.split('/')[2]
        response = transcribe_client.start_transcription_job(
            TranscriptionJobName=job_name,
            IdentifyLanguage=True,
            MediaFormat=codec,
            Media={'MediaFileUri': s3_path_in},
            OutputBucketName=bucket_name,
            OutputKey=output_key 
        )
        
        job_name = response['TranscriptionJob']['TranscriptionJobName']
        job = transcribe_client.get_transcription_job(TranscriptionJobName=job_name)
        job_status = job['TranscriptionJob']['TranscriptionJobStatus']
        
        logger.info(f"Transcription job {job_name} started with status: {job_status}")
        return job_status
    except Exception as e:
        logger.error(f"Error starting transcription job: {str(e)}")
        raise
