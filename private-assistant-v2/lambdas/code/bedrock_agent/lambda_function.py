################################################
## This function queries Amazon Bedrock Agent ##
################################################
import boto3
import os
import json
import logging
from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Configuration class
@dataclass
class Config:
    model_id: str
    key_name_active_connections: str
    table_name: str
    agent_id: str
    agent_alias_id: str
    bucket_name: str
    base_path: str = "/tmp/"

    @classmethod
    def from_env(cls):
        return cls(
            model_id=os.environ['ENV_MODEL_ID'],
            key_name_active_connections=os.environ['ENV_KEY_NAME'],
            table_name=os.environ["TABLE_NAME"],
            agent_id=os.environ['ENV_AGENT_ID'],
            agent_alias_id=os.environ['ENV_ALIAS_ID'],
            bucket_name=os.environ["BUCKET_NAME"]
        )

# AWS Service clients
class AWSClients:
    def __init__(self):
        self.sm_client = boto3.client("socialmessaging")
        self.s3_client = boto3.client('s3')
        self.bedrock_client = boto3.client(service_name="bedrock-runtime")
        self.bedrock_agent_client = boto3.client('bedrock-agent-runtime')
        self.dynamodb = boto3.resource("dynamodb")

# Database operations class
class DynamoDBOperations:
    def __init__(self, table):
        self.table = table

    def update_item(self, value: str, message_history: List[Dict]) -> Dict:
        try:
            response = self.table.update_item(
                Key={"id": value},
                UpdateExpression="set message_history=:message_history",
                ExpressionAttributeValues={':message_history': message_history},
                ReturnValues="UPDATED_NEW"
            )
            logger.info(f"Item updated successfully: {response}")
            return response
        except Exception as e:
            logger.error(f"Error updating item: {str(e)}")
            raise

    def query(self, key_name: str, keyvalue: str) -> Dict:
        try:
            response = self.table.query(
                KeyConditionExpression=Key(key_name).eq(keyvalue)
            )
            logger.info(f"Query successful: {response}")
            return response['Items'][0]
        except Exception as e:
            logger.error(f"Error querying item: {str(e)}")
            raise

    def save(self, item: Dict) -> None:
        try:
            response = self.table.put_item(Item=item)
            logger.info(f"Item saved successfully: {response}")
        except Exception as e:
            logger.error(f"Error saving item: {str(e)}")
            raise

# Message handling class
class WhatsAppMessageHandler:
    def __init__(self, clients: AWSClients):
        self.clients = clients

    def text_reply(self, phone_number: str, message_id: str, 
                  phone_number_id: str, text_message: str) -> Dict:
        message_object = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "context": {"message_id": message_id},
            "to": f"+{phone_number}",
            "type": "text",
            "text": {"preview_url": False, "body": text_message},
        }
        
        kwargs = {
            "originationPhoneNumberId": phone_number_id,
            "metaApiVersion": "v20.0",
            "message": bytes(json.dumps(message_object), "utf-8"),
        }
        
        try:
            response = self.clients.sm_client.send_whatsapp_message(**kwargs)
            logger.info(f"Message sent successfully: {response}")
            return response
        except Exception as e:
            logger.error(f"Error sending message: {str(e)}")
            raise


class BedrockOperations:
    def __init__(self, clients: AWSClients, config: Config):
        self.clients = clients
        self.config = config

    def invoke_agent(self, session_id: str, prompt: str, 
                    phone_number: str, db_ops: DynamoDBOperations) -> str:
        #https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/bedrock-agent-runtime/client/invoke_agent.html
        try:
            request_params = {
                'agentId': self.config.agent_id,
                'agentAliasId': self.config.agent_alias_id,
                'sessionId': session_id,
                'inputText': prompt,
            }
            
            # Add conversation history if available
    
            try:
                whatsapp_data = db_ops.query(
                    self.config.key_name_active_connections, 
                    phone_number
                )
                logger.info(f'whatsapp_data: {whatsapp_data}')
        
            
                if whatsapp_data.get('message_history'):
                    request_params['sessionState'] = {
                        'conversationHistory': {
                            'messages': whatsapp_data['message_history']
                        }
                    }
            except:
                logger.info(f"No message history found.")


            logger.info(f'request_params: {request_params}')
            
            response = self.clients.bedrock_agent_client.invoke_agent(**request_params)
            logger.info(f'response: {response}')

            completion = "".join(
                event["chunk"]["bytes"].decode() 
                for event in response.get("completion", [])
            )
            return completion

        except Exception as e:
            logger.error(f"Error invoking agent: {str(e)}")
            raise
        
    def invoke_converse(self,input_text: str, byte_image: str,media_type: str,media_format: str,document=None) -> str:
        print("media_type: ", media_type)
        try:
            if document:
                media_converse = {
                                'document': {
                                    "format": media_format,
                                    'name': document,
                                    "source": {"bytes": byte_image}
                                }
                        }

            else:
                if media_type == "video":
                    media_converse = {
                                    'video': {
                                        "format": media_format,
                                        "source": {'s3Location': {
                                            'uri': byte_image
                                            }
                                            }
                                        }
                                    }
                else: 
                    media_converse = {
                                    f"{media_type}": {
                                        "format": f"{media_format}",
                                        "source": {"bytes": byte_image}
                                    }
                            }

            message = {
                    "role": "user",
                    "content": [
                        {
                            "text": input_text
                        },
                        media_converse
                    ]
                }
            messages = [message]
            # Send the message.
            response = self.clients.bedrock_client.converse(
                modelId=self.config.model_id,
                messages=messages,
                system = [{"text": "Always answer in the same language you are asked."}]
                                )
            print("response: ", response)
            content_assistan = response['output']['message']
            text_message = response['output']['message']['content'][0]['text']
            return content_assistan,text_message
            
        except ClientError as e:
            text_message = f"Error invoking agent: {str(e)}"
            print(f"Error invoking agent: {str(e)}")
            content_assistan = None
            raise
    
class S3Operations:
    def __init__(self, clients: AWSClients, config: Config):
        self.clients = clients
        self.config = config

    def get_image_from_s3(self,image_key):
        """Retrieve image from S3 bucket"""
        try:
            response = self.clients.s3_client.get_object(
                Bucket=self.config.bucket_name,
                Key=image_key
            )
            image_data = response['Body'].read()
            return image_data
        except ClientError as e:
            logger.error(f"Error invoking agent: {str(e)}")
            raise 
     
# Main handler class
class LambdaHandler:
    def __init__(self):
        self.config = Config.from_env()
        self.clients = AWSClients()
        self.db_ops = DynamoDBOperations(
            self.clients.dynamodb.Table(self.config.table_name)
        )
        self.message_handler = WhatsAppMessageHandler(self.clients)
        self.bedrock_ops = BedrockOperations(self.clients, self.config)
        self.s3_ops = S3Operations(self.clients, self.config)

    def handle(self, event: Dict, context: Any) -> Dict:
        logger.info(f'REQUEST RECEIVED: {event}')
        
        message = event['message']
        phone_number = message['from']
        message_id = message['id']
        message_type = message['type']
        phone_number_id = event['phone_number_id']
        logger.info(f'type: {message_type}')

        if message_type == "text":
            prompt = message['text']['body']
            text_message = self.bedrock_ops.invoke_agent(
                phone_number, prompt, phone_number, self.db_ops
            )
        else:
            try:
                try:
                    input_text = message[message_type]['caption'] 
                except:
                    input_text = f"Describe this {message_type}?"

                logger.info(f'input_text: {input_text}')

                s3_uri = event['message']["location"]
                logger.info(f's3_uri: {s3_uri}')
                key = "/".join(s3_uri.split("/")[3:])
                media_format = s3_uri.split(".")[-1]
                if message_type == "image" or message_type == "video":
                    byte_image = self.s3_ops.get_image_from_s3(key)
                    if message_type == "video":
                        byte_image = s3_uri    
                    content_assistan,text_message = self.bedrock_ops.invoke_converse(input_text, byte_image,message_type,media_format)
                elif message_type == "document":
                    byte_image = self.s3_ops.get_image_from_s3(key)
                    document = s3_uri.split("/")[-1].split(".")[0]
                    print(media_format)
                    print(document)
                    content_assistan,text_message = self.bedrock_ops.invoke_converse(input_text, byte_image,message_type,media_format,document)

                print("text_message: ", text_message)
                prompt_to_agent = f" Some time ago you had the ability to process {message_type}, you were sent one and asked this question: {input_text}. To which you replied: {text_message}. If you are asked something related, look for the answer in this answer you gave." 
                message_history = build_history(prompt_to_agent,content_assistan)
                try:
                    tabla_value = {"phone_number" : phone_number,
                    "message_history" : message_history}
                    self.db_ops.save(tabla_value)
                    print("New Item")
                except:
                    self.db_ops.update_item(phone_number,message_history,table)
                    print("Update Item conversation")

            except:
                print(f"Unsupported message type: {message_type}")
                # Handle non-text messages (implementation details omitted for brevity)
                text_message = f"Unsupported message type: {message_type}"


        self.message_handler.text_reply(
            phone_number, message_id, phone_number_id, text_message
        )
        
        return {"statusCode": 200}

# Lambda handler function
def lambda_handler(event: Dict, context: Any) -> Dict:
    
    handler = LambdaHandler()
    return handler.handle(event, context)

def build_history(image_prompt,content_assistan):
    message_history = [
                    {
                        'content': [
                            {
                                'text': image_prompt
                            },
                        ],
                        'role': 'user'
                    },
                    
                        content_assistan
                    ,
                ]
    return message_history
