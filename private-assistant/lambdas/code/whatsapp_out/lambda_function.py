
import boto3
import json
import os
import requests
from boto3.dynamodb.conditions import Key
from utils import ( normalize_phone,)

base_path="/tmp/"

def whats_out(phone, whats_token, phone_id, message, in_reply_to):
    
    # https://developers.facebook.com/docs/whatsapp/cloud-api/reference/messages#reply-to-message
    URL = 'https://graph.facebook.com/v15.0/'+phone_id+'/messages'
    headers = {'Authorization': whats_token, 'Content-Type': 'application/json'}
    data = { 
        "messaging_product": "whatsapp", 
        "to": normalize_phone(phone), 
        "context":  json.dumps({ "message_id": in_reply_to}),
        "type": "text", 
        "text": json.dumps({ "preview_url": False, "body": message})
    }
    
    print("Sending")
    print(data)
    response = requests.post(URL, headers=headers, data=data)
    responsejson = response.json()
    print("Responses: "+ str(responsejson)
    )

def lambda_handler(event, context):

    print (event)
    
    phone = event['phone']
    whats_token = event['whats_token']
    phone_id = event['phone_id']
    message = event['message']
    in_reply_to = event['in_reply_to']
    
    try:
        whats_out(phone, whats_token, phone_id, message, in_reply_to)
        return True
            
    except Exception as error: 
        print('FAILED!', error)
        return True