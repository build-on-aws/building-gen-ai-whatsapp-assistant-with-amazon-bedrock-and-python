################################################
## This function queries Amazon Bedrock Agent ##
################################################
import boto3
import os
import uuid
import sys
import json

from botocore.exceptions import ClientError
sm_client = boto3.client("socialmessaging")

bedrock_agent_client = boto3.client('bedrock-agent-runtime')
agent_id = os.environ.get('ENV_AGENT_ID')
agent_alias_id = os.environ.get('ENV_ALIAS_ID')
BUCKET_NAME = os.environ.get("BUCKET_NAME")
s3 = boto3.client('s3')
base_path="/tmp/"


def text_reply(phone_number,message_id, phone_number_id,text_message):
        print("reply message...")
        message_object = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "context": {"message_id": message_id},
            "to": f"+{phone_number}",
            "type": "text",
            "text": {"preview_url": False, "body": text_message},
        }
        print("message_object: ", message_object)

        kwargs = dict(
            originationPhoneNumberId=phone_number_id,
            metaApiVersion="v20.0",
            message=bytes(json.dumps(message_object), "utf-8"),
        )
        print(kwargs)
        response = sm_client.send_whatsapp_message(**kwargs)
        print("replied to message:", response)
        # message_object["id"] = response.get("messageId")
        # message_object["from"] = self.phone_number
        # replied_message = WhatsappMessage(self.meta_phone_number, message_object , self.metadata)
        # return replied_message

def invoke_agent(agent_id, agent_alias_id, session_id, prompt, image_data=None):
     #https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/bedrock-agent-runtime/client/invoke_agent.html
     try:
        request_params = {
            'agentId': agent_id,
            'agentAliasId': agent_alias_id,
            'sessionId': session_id,
            'inputText': prompt,

        }
        
        if image_data:
            request_params['sessionState'] = {
                'files': [
            {
                'name': 'picture',
                'source': {
                    's3Location': {
                        'uri': f'{image_data}'
                    },
                    'sourceType': 'S3'
                },
                'useCase': 'CHAT'
            }
        ]
            }
        
        response = bedrock_agent_client.invoke_agent(**request_params)
        print("response: ",response)

        completion = ""

        for event in response.get("completion"):
            chunk = event["chunk"]
            completion = completion + chunk["bytes"].decode()
        
        
        print(completion)
        return completion

     except:
        print(f"Couldn't invoke agent.")
        raise
     

def lambda_handler(event, context):
    print('REQUEST RECEIVED:', event)
    message = event['message']
    phone_number = event['message']['from']
    print("message: ", message)
    message_id = message['id']
    message_type = message['type']
    phone_number_id = event['phone_number_id']
    print("type: ",message_type)
    if message_type == "image":
        prompt = message['image']['caption'] if message['image']['caption'] else "What do you see in this image?"
        print("prompt: ", prompt)
        image_key = event['message']["location"]
        # Get image from S3
        #print("image_key: ", image_key)
        #print("BUCKET_NAME: ", BUCKET_NAME)
        #response = s3.get_object(Bucket=BUCKET_NAME, Key=image_key)
        #image_data = response['Body'].read()
        text_message = invoke_agent(agent_id, agent_alias_id, phone_number, prompt, image_data=image_key)

    elif message_type == "text" or message_type == "audio":
         prompt = message['text']['body']
         text_message = invoke_agent(agent_id, agent_alias_id, phone_number, prompt,image_data=None)

    else:
         print("ese formato no")
         text_message = f"Bad message type: {message_type}"
    
        
    text_reply(phone_number,message_id,phone_number_id, text_message)

    
    return