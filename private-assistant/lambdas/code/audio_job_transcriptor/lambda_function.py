import boto3
import os

import time
import sys
import datetime
import uuid
from botocore.exceptions import ClientError
import re


from file_utils import( get_media_url , get_whats_media,put_file)

base_path="/tmp/"

SOURCE_LANG_CODE = os.environ.get('SOURCE_LANG_CODE')

BucketName = os.environ.get('BucketName')
AudioKeyName = os.environ.get('AudioKeyName')
TextBucketName = os.environ.get('TextBucketName')

table_name_active_connections = os.environ.get('whatsapp_MetaData')
key_name_active_connections = "messages_id"

dynamodb_resource=boto3.resource('dynamodb')
table = dynamodb_resource.Table(table_name_active_connections)
key_name_active_connections = "messages_id"

transcribe_client  = boto3.client('transcribe')
client_s3 = boto3.client('s3')

#https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/transcribe/client/start_transcription_job.html

def db_update_item(value,jobName,now):
    print("Update jobname")
    try:
        response = table.update_item(
            Key={
                    "messages_id" : value
                },
                UpdateExpression="set jobName=:item1, now=:item2",
                ExpressionAttributeValues={
                    ':item1': jobName,
                    ':item2': now,
                },
                ReturnValues="UPDATED_NEW")
        print (response)
    except Exception as e:
        print (e)
    else:
        return response
            

def start_job_transciptor (jobName,s3Path_in,OutputKey,codec):
    print(s3Path_in)
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

    
def lambda_handler(event, context):

    print(event)

    start = int( time.time() )
    whats_message = event['whats_message']

    whats_token = event['whats_token']
    messages_id = event['messages_id']
    phone = event['phone']
    phone_id = event['phone_id']
    
    messageType = whats_message['type']
    
    fileType = whats_message[messageType]['mime_type']
    fileExtension = fileType.split('/')[-1]
    fileId = whats_message[messageType]['id']
    fileName = f'{fileId}.{fileExtension}'
    fileUrl = get_media_url(fileId, whats_token)  
    
    mime_type = fileType.split(";")[0]
    codec = mime_type.split("/")[-1]
    print(codec)
    
    if not fileUrl: return
    
    fileContents = get_whats_media(fileUrl,whats_token)
    fileSize = sys.getsizeof(fileContents) - 33 ## Removing BYTES overhead


    print(f"messageType:{messageType}")
    print(f"fileType:{fileType}")
    print(f"fileName:{fileName}")
    print(f"fileId:{fileId}")
    print(f"fileUrl:{fileUrl}")
    print("Size downloaded:" + str(fileSize))
    
    print ("Ready To TRANSCRIPTION!")
    
    #audio_decoded = base64.b64decode(fileContents)

    now = int( time.time() )
    
    LOCAL_FILE = f"audio_{fileId}.{codec}"
    
    with open(f"{base_path}{LOCAL_FILE}", "wb") as binary_file:
        binary_file.write(fileContents) 

    put_file(base_path,LOCAL_FILE, BucketName, AudioKeyName+"/")

    s3Path_in = "s3://" + BucketName + "/" + AudioKeyName +"/"+LOCAL_FILE

    jobName = fileId 

    bucket_key_out = TextBucketName +"/" + f"texto_{fileId}"

    start_job_transciptor (jobName,s3Path_in,bucket_key_out,codec)
    
    value = whats_message['id'].strip().replace(" ","")
    jobName= jobName.strip().replace(" ","")
    print(value)
    print(jobName)
    print(now)
    db_update_item(value,jobName,now)


    return True

