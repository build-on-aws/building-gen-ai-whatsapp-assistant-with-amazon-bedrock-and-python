
import boto3
import json
import os
import requests
from boto3.dynamodb.conditions import Key
from utils import (normalize_phone,get_config,whats_reply)
from botocore.exceptions import ClientError

lambda_client = boto3.client('lambda')

from db_utils import query_gd, query

from file_utils import download_file

table_name_active_connections = os.environ.get('whatsapp_MetaData')

key_name_active_connections = os.environ.get('ENV_KEY_NAME')
Index_Name = os.environ.get('ENV_INDEX_NAME')
whatsapp_out_lambda = os.environ.get('WHATSAPP_OUT')
LAMBDA_AGENT_TEXT = os.environ['ENV_LAMBDA_AGENT_TEXT']

client_s3 = boto3.client('s3')
dynamodb_resource=boto3.resource('dynamodb')
table = dynamodb_resource.Table(table_name_active_connections)

base_path="/tmp/"



def lambda_handler(event, context):

    print (event)

    for record in event['Records']:
        print("Event: ",event['Records'])
        record = event['Records'][0]
    
        s3bucket = record['s3']['bucket']['name']
        s3object = record['s3']['object']['key']
        filename = s3object.split("/")[-1]
        keyvalue = s3object.split("/")[-2]

        key = s3object.split("/")[1]+"/"
        print("s3object: ",s3object)
        print("filename: ",filename)
        print("key: ",key)

        if os.path.splitext(filename)[1] != ".temp":

            download_file(base_path,s3bucket, s3object, filename)
            value = filename.split("_")[-1].replace(".txt","").strip().replace(" ","")
            print(value)

            with open(base_path+filename) as f:
                message = f.readlines()

            messages_id = query_gd("jobName",table,value,Index_Name)[key_name_active_connections]
            whatsapp_data = query(key_name_active_connections,table,messages_id)
            message_json = json.loads(message[0])
            print(message_json)
            text = message_json["results"]['transcripts'][0]['transcript']
            phone = '+' + str(whatsapp_data['changes'][0]["value"]["messages"][0]["from"])
            phone_number = str(whatsapp_data['changes'][0]["value"]["messages"][0]["from"])
            whats_token = whatsapp_data['whats_token']
            phone_id = whatsapp_data['changes'][0]["value"]["metadata"]["phone_number_id"]

            try:
                print('REQUEST RECEIVED:', event)
                print('REQUEST CONTEXT:', context)
                print("PROMPT: ",text)

                whats_reply(whatsapp_out_lambda,phone, whats_token, phone_id, f"{text}", keyvalue)

                #remove this comment if you want to send voice notes to the agent!

                """ 
                try:       

                    response_3 = lambda_client.invoke(
                        FunctionName = LAMBDA_AGENT_TEXT,
                        InvocationType = 'Event' ,#'RequestResponse', 
                        Payload = json.dumps({
                            'whats_message': text,
                            'whats_token': whats_token,
                            'phone': phone,
                            'phone_id': phone_id,
                            'messages_id': messages_id

                        })
                    )

                    print(f'\nRespuesta:{response_3}')

                    return response_3
                    
                except ClientError as e:
                    err = e.response
                    error = err
                    print(err.get("Error", {}).get("Code"))
                    return f"Un error invocando {LAMBDA_AGENT_TEXT}
                """
            
            except Exception as error: 
                print('FAILED!', error)
                return True
            
        else:
            print("No text file")
            return True
