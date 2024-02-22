
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
##++++++ Amazon Lambda Function for processing WhatsApp incoming messages +++++
## Updated to Whatsapp API v14
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

import json
import os
import boto3
from botocore.exceptions import ClientError
import time

from utils import ( get_config,build_response,validate_healthcheck)

table_name_active_connections = os.environ.get('whatsapp_MetaData') 
#whatsapp_MetaData_follow = os.environ.get('whatsapp_MetaData_follow')
key_name_active_connections = "messages_id"

dynamodb_resource=boto3.resource('dynamodb')
table = dynamodb_resource.Table(table_name_active_connections)

valid_display_phone_number = os.environ.get('DISPLAY_PHONE_NUMBER') 

CONFIG_PARAMETER= os.environ['CONFIG_PARAMETER']

def batch_put_items(client, table_name, item_arrays):
    table = client.Table(table_name)
    with table.batch_writer() as batch:
        for itm in item_arrays:
            res = batch.put_item(Item=itm)
            print(res)


def lambda_handler(event, context):
    print (event)
    connect_config=json.loads(get_config(CONFIG_PARAMETER))

    if event['httpMethod'] == 'GET':
        return build_response(200, 
            validate_healthcheck(event, connect_config['WHATS_VERIFICATION_TOKEN']))

    if event.get("body") == None: build_response(200,"bye bye")

    body = json.loads(event['body'])
    WHATS_TOKEN = 'Bearer ' + connect_config['WHATS_TOKEN']

    ##WhatsApp specific iterations. 
    for entry in body['entry']:
        print("Iterating entry")
        print(entry)
        display_phone_number=entry["changes"][0]["value"]["metadata"]["display_phone_number"]
        timestamp = int(entry["changes"][0]["value"]["messages"][0]["timestamp"])
        now = int(time.time())
        diferencia = now - timestamp
        if diferencia > 300:  #session time in seg
            print("old message")
            break
        
        if display_phone_number == valid_display_phone_number:
            try:
                entry[key_name_active_connections]=entry["changes"][0]["value"]["messages"][0]["id"]
                entry["whats_token"] = WHATS_TOKEN
                print("key_name_active_connections",entry[key_name_active_connections])
                batch_put_items(dynamodb_resource, table_name_active_connections, [entry])
                #batch_put_items(dynamodb_resource, whatsapp_MetaData_follow, [entry])
            except:
                print("No messages")
        else: 
            print("No valid diplay phone number: ", display_phone_number)
            
                
    return build_response(200,"OK")
