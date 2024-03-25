##########################################################################
## This function queries anthropic.claude-3-sonnet - Q&A without memory ##
##########################################################################

import json
import boto3
import os
import time
import base64
import sys
import requests
from file_utils import(get_media_url , get_whats_media, put_file)
from db_utils import (update_items_out,save_item_ddb,query,update_item_session)
from utils import whats_reply
from boto3.dynamodb.conditions import Key

BucketName = os.environ.get('BucketName')
ImageKeyName = os.environ.get('ImageKeyName')
model_id = os.environ.get('ENV_MODEL_ID_IMAGE')
accept = 'application/json'
contentType = 'application/json'
anthropic_version = os.environ.get('ENV_ANTHROPIC_VERSION')

whatsapp_out_lambda = os.environ.get('WHATSAPP_OUT')
table_name_active_connections = os.environ.get('whatsapp_MetaData')


client_s3 = boto3.client('s3')
dynamodb_resource=boto3.resource('dynamodb')
bedrock_client = boto3.client("bedrock-runtime")

base_path="/tmp/"
table = dynamodb_resource.Table(table_name_active_connections)
table_name_session = os.environ.get('session_table_history')
table_session_active = dynamodb_resource.Table(os.environ['user_sesion_metadata'])

def add_text(role, content, history):
    print("expand history items into new_history")
    # expand history items into new_history
    new_history = [h for h in history]
    new_history.append({"role":role,"content":content})
    return new_history

def save_history(table,item):
    print("put item")
    table_session_active = dynamodb_resource.Table(table)
    response = table_session_active.put_item(Item=item)
    print(response)
    return True
    
def load_history(table, sessionid):
    response = table.get_item(Key={"id": sessionid})
    return response.get("Item")
    
def query_history(key,table,keyvalue):
    print("Query History")
    table_session_active = dynamodb_resource.Table(table)
    response = table_session_active.query(
        KeyConditionExpression=Key(key).eq(keyvalue)
    )
    print(response)
    return response['Items'][0]


def process_image(messageType,whats_token,ImageKeyName,whats_message):
    print(f"messageType:{messageType}")
    fileType = whats_message['mime_type']
    print(f"fileType:{fileType}")
    fileExtension = fileType.split('/')[-1]
    fileId = whats_message['id']
    print(f"fileId:{fileId}")
    fileName = f'{fileId}.{fileExtension}'
    print(f"fileName:{fileName}")
    whats_message =whats_message['caption']
    print(f"caption:{whats_message}")

    fileUrl = get_media_url(fileId, whats_token) 
    if not fileUrl: return
    fileContents = get_whats_media(fileUrl,whats_token)
    fileSize = sys.getsizeof(fileContents) - 33 ## Removing BYTES overhead
    print(f"fileSize:{fileSize}")
    print ("Image Ready!")

    now = int( time.time() )
    LOCAL_FILE = f"image_{fileName}"
    print(f"LOCAL_FILE:{LOCAL_FILE}")

    with open(f"{base_path}{LOCAL_FILE}", "wb") as binary_file:
        binary_file.write(fileContents) 

    put_file(base_path,LOCAL_FILE, BucketName, ImageKeyName+"/")
    return(LOCAL_FILE,whats_message)

def agent_image(model_id, anthropic_version, max_tokens,image_path,text,history):
    with open(image_path, "rb") as image_file:
        content_image = base64.b64encode(image_file.read()).decode('utf8')
    content = [
        {"type": "image", "source": {"type": "base64",
            "media_type": "image/jpeg", "data": content_image}},
        {"type":"text","text":text}
        ]
    new_history = add_text("user",content, history)
    body = {
        "system": "You are an AI Assistant, always reply in the original user text language.",
        "messages":new_history,"anthropic_version": anthropic_version,"max_tokens":max_tokens}
    
    response = bedrock_client.invoke_model(body=json.dumps(body), modelId=model_id, accept=accept, contentType=contentType)
    response_body = json.loads(response.get('body').read())
    assistant_text = response_body.get("content")[0].get("text")
    new_history = add_text("assistant", assistant_text, new_history)
    
    return assistant_text, new_history



def lambda_handler(event, context):
    print (event)

    whats_message = event['whats_message']
    print(whats_message)
    print('REQUEST RECEIVED:', event)
    print('REQUEST CONTEXT:', context)
    print("PROMPT: ",whats_message)

    messageType = event['type']
    print("type: ",messageType)
    
    try:
        whats_token = event['whats_token']
        messages_id = event['messages_id']
        phone = event['phone']
        phone_id = event['phone_id']
        phone_number = phone.replace("+","")
        session_data = query("phone_number",table_session_active,phone_number)
        now = int(time.time())
        diferencia = now - session_data["session_time"]
        if diferencia > 240:  #session time in seg
            print("Mayor de 240")
            update_item_session(table_session_active,phone_number,now)
            id = str(phone_number) + "_" + str(now)
            history = []
        else:
            print("Menor de 240")
            id = str(phone_number) + "_" + str(session_data["session_time"])
            history = query_history("SessionId",table_name_session,id)["History"]
            print(history)
           
    except:
        print("Nuevo")
        now = int(time.time())
        new_row = {"phone_number": phone_number, "session_time":now}
        save_item_ddb(table_session_active,new_row)
        history = []
        id = str(phone_number) + "_" + str(now)

    try:
        #s = re.sub(r'[^a-zA-Z0-9]', '', query)

        print(messageType)
        print(whats_message["image"])
        max_tokens=500
        LOCAL_FILE,prompt = process_image(messageType,whats_token,ImageKeyName,whats_message["image"])
        print(LOCAL_FILE)
        response,history = agent_image(model_id, anthropic_version, max_tokens,f"{base_path}{LOCAL_FILE}",prompt,history)
        print(response)
       
        whats_reply(whatsapp_out_lambda,phone, whats_token, phone_id, f"{response}", messages_id)
        end = int( time.time())
        update_items_out(table,messages_id,response,end)   
        item = {"SessionId":id,"History" : history}
        save_history(table_name_session,item)
        
        return({"body":response})    
        
    except Exception as error: 
            print('FAILED!', error)
            return({"body":"Cuek! I dont know"})
