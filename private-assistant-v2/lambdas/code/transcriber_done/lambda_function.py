
import boto3
import json
import os
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

lambda_client = boto3.client('lambda')
dynamodb = boto3.resource("dynamodb")
client_s3 = boto3.client('s3')

TABLE_NAME = os.environ.get("TABLE_NAME")
table = dynamodb.Table(TABLE_NAME)
key_name_active_connections = os.environ.get('ENV_KEY_NAME')
Index_Name = os.environ.get('ENV_INDEX_NAME')

LAMBDA_BEDROCK_AGENT = os.environ['ENV_LAMBDA_BEDROCK_AGENT'] 

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
                message_text = f.readlines()

            message={}
            message['text'] = {}

            messages_id = query_gd("jobName",table,value,Index_Name)[key_name_active_connections]
            whatsapp_data = query(key_name_active_connections,table,messages_id)
            message_json = json.loads(message_text[0])
            print("message_json: ",message_json)
            print("whatsapp_data: ",whatsapp_data)
            message['text']['body'] = message_json["results"]['transcripts'][0]['transcript']
            phone_number_id = str(whatsapp_data['eum_phone_number'])
            message["from"] = str(whatsapp_data['from'])
            message['id'] = str(whatsapp_data['id'])
            message['type'] = "text"
            print("message: ",message)

            try:
                print('REQUEST RECEIVED:', event)
                print('REQUEST CONTEXT:', context)
                print("PROMPT: ",message['text']['body'])

                data = {
                    'message': message,
                    'phone_number_id' : phone_number_id,
                            }
                invoke_other_lambda(data,LAMBDA_BEDROCK_AGENT)


            except Exception as error: 
                print('FAILED!', error)
                return True
            
        else:
            print("No text file")
            return True
        
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
    
def download_file(base_path,bucket, key, filename):
    print("Download file from s3://{}{}".format(bucket,key))
    with open(base_path+filename, "wb") as data:
        client_s3.download_fileobj(bucket, key, data)
    print("Download file from s3://{}{}".format(bucket,key))
    return True

def query_gd(key,table,keyvalue,Index_Name):
    resp = table.query(
    # Add the name of the index you want to use in your query.
    IndexName=Index_Name,
    KeyConditionExpression=Key(key).eq(keyvalue),
    )
    print(resp)
    return resp['Items'][0]

def query(key,table,keyvalue):
    response = table.query(
        KeyConditionExpression=Key(key).eq(keyvalue)
    )
    print(response)
    return response['Items'][0]