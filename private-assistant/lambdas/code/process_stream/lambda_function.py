#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
##++++++ Amazon Lambda Function for processing WhatsApp incoming messages +++++
## Updated to Whatsapp API v14
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

import boto3
from boto3.dynamodb.types import TypeDeserializer
import decimal
import json
import os

import requests
from botocore.exceptions import ClientError

lambda_client = boto3.client('lambda')

from file_utils import( get_media_url )

from utils import (build_response)

SUPPORTED_FILE_TYPES = ['text/csv','image/png','image/jpeg','application/pdf']


def ddb_deserialize(r, type_deserializer = TypeDeserializer()):
    return type_deserializer.deserialize({"M": r})

class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            if o % 1 > 0:
                return float(o)
            else:
                return int(o)
        return super(DecimalEncoder, self).default(o)

def lambda_handler(event, context):
    print (event)

    for rec in event['Records']:

        try:               
            entry = json.loads(json.dumps(ddb_deserialize(rec['dynamodb']['NewImage']), cls=DecimalEncoder))
            messages_id = entry["messages_id"]
            event_name = rec['eventName']
            print(event_name)
            
            if event_name == "INSERT":
                print("messages_id: ", messages_id)
                print("entry: ",entry)
                WHATS_TOKEN = entry["whats_token"]
    
                for change in entry['changes']:
                    print("Iterating change")
                    print(change)
                    ## Skipping as no contact info was relevant.
                    if('contacts' not in change['value']):
                        continue
                        
                    whats_message = change['value']['messages'][0]
    
                    phone_id = change['value']['metadata']['phone_number_id']
                    name = change['value']['contacts'][0]['profile']['name']
                    phone = '+' + str(whats_message['from'])
                    channel = 'whatsapp'
    
                    ##Define message type
                    messageType =whats_message['type']
                    if(messageType == 'text'):
                        message = whats_message['text']['body']
                        process_text(message, WHATS_TOKEN,phone,phone_id,messages_id)
    
                        
                    # Agregar para respuestas a boton!    
                    elif(messageType == 'button'):
                        message =whats_message['button']['text']
                    
                    elif(messageType == 'audio'):
                        #processed_audio = process_audio(whats_message, WHATS_TOKEN,phone,systemNumber)
                        processed_job_audio = star_job_audio(whats_message, WHATS_TOKEN,phone,phone_id,messages_id)
                        
                        message = "Procesando.."
                    else:
                        message = 'Attachment'
                        fileType = whats_message[messageType]['mime_type']
                        fileName = whats_message[messageType].get('filename',phone + '.'+fileType.split("/")[1])
                        fileId = whats_message[messageType]['id']
                        fileUrl = get_media_url(fileId,WHATS_TOKEN)
                        
                        print(fileType)
                    print(message, messageType, name, phone_id)
                    print(build_response (200,json.dumps('All good!')))
            else: 
                print("no New INSERT")
        except:
            print("no New Image")
        
        return True

            

def process_text(whats_message, whats_token,phone,phone_id,messages_id):

    print("text", whats_message, whats_token)
    LAMBDA_AGENT_TEXT = os.environ['ENV_LAMBDA_AGENT_TEXT']
    
    try:       

        response_3 = lambda_client.invoke(
            FunctionName = LAMBDA_AGENT_TEXT,
            InvocationType = 'Event' ,#'RequestResponse', 
            Payload = json.dumps({
                'whats_message': whats_message,
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
        return f"Un error invocando {LAMBDA_AGENT_TEXT}"
   
    
def star_job_audio(whats_message, whats_token,phone,phone_id,messages_id):

    print("audio", whats_message, whats_token)
    JOB_TRANSCRIPTOR_LAMBDA = os.environ['JOB_TRANSCRIPTOR_LAMBDA']
    
    try:       

        response_2 = lambda_client.invoke(
            FunctionName = JOB_TRANSCRIPTOR_LAMBDA,
            InvocationType = 'Event' ,#'RequestResponse', 
            Payload = json.dumps({
                'whats_message': whats_message,
                'whats_token': whats_token,
                'phone': phone,
                'phone_id': phone_id,
                'messages_id': messages_id

            })
        )

        print(f'\nRespuesta:{response_2}')

        return response_2
        
    except ClientError as e:
        err = e.response
        error = err
        print(err.get("Error", {}).get("Code"))
        return f"Un error invocando {JOB_TRANSCRIPTOR_LAMBDA}"