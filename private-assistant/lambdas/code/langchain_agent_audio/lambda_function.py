#################################################
## This function is to query a dynamoDB table ###
#################################################

import json
import boto3
import os
import requests
import time

from db_utils import query, query_gd,save_item_ddb,update_items_out,update_item_session

from agent_utils import match_function, memory_dynamodb,langchain_agent
from file_utils import download_file

from langchain.agents import load_tools, initialize_agent, AgentType,Tool
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory
from langchain.memory.chat_message_histories import DynamoDBChatMessageHistory
from langchain.llms.bedrock import Bedrock
from boto3.dynamodb.conditions import Key
from utils import ( normalize_phone,get_config)

client_s3 = boto3.client('s3')
dynamodb_resource=boto3.resource('dynamodb')
bedrock_client = boto3.client("bedrock-runtime")

table_name_active_connections = os.environ.get('whatsapp_MetaData')

table_session_active = dynamodb_resource.Table(os.environ['TABLE_SESSION_ACTIVE'])
key_name_active_connections = os.environ.get('ENV_KEY_NAME')
Index_Name = os.environ.get('ENV_INDEX_NAME')

base_path="/tmp/"

table_name_session = os.environ.get('TABLE_SESSION')
model_id = os.environ.get('ENV_MODEL_ID')

table = dynamodb_resource.Table(table_name_active_connections)


model_parameter = {"temperature": 0.0, "top_p": .9, "max_tokens_to_sample": 2000}
llm = Bedrock(model_id=model_id, model_kwargs=model_parameter,client=bedrock_client)

def promp_definition():

    prompt_template = """
        You are an assistant who answers information about passenger status, and also do casual conversation. 
        Use the following format:
        History: the context of a previous conversation with the user. Useful if you need to recall past conversation, make a summary, or rephrase the answers. if History is empty it continues.
        Question: the input question you must answer
        Thought: you should always think about what to do, Also try to follow steps mentioned above. You must undestand the identification number as Alphanumeric, only numbers and letters, no words.
        Action: the action to take, should be one of ["search-passanger-information"]
        Action Input: the input to the action
        Observation: the result of the action
        Thought: I now know the final answer
        Final Answer: the final answer to the original input question, always reply in the original user language and human legible.

        History: 
        {chat_history}

        Question: {input}

        Assistant:
        {agent_scratchpad}"""

    updated_prompt = PromptTemplate(
    input_variables=['chat_history','input', 'agent_scratchpad'], template=prompt_template)

    return updated_prompt

def whats_reply(phone, whats_token, phone_id, message, in_reply_to):
    
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
            
            value = filename.split("_")[-1].replace(".txt","")
            print(value)

            with open(base_path+filename) as f:
                message = f.readlines()

            messsange_id = query_gd("jobName",table,value,Index_Name)[key_name_active_connections]
            whatsapp_data = query(key_name_active_connections,table,messsange_id)
            message_json = json.loads(message[0])
            text = message_json["results"]['transcripts'][0]['transcript']
            phone = '+' + str(whatsapp_data['changes'][0]["value"]["messages"][0]["from"])
            phone_number = str(whatsapp_data['changes'][0]["value"]["messages"][0]["from"])
            whats_token = whatsapp_data['whats_token']
            phone_id = whatsapp_data['changes'][0]["value"]["metadata"]["phone_number_id"]

            try:
                session_data = query("phone_number",table_session_active,phone_number)
                now = int(time.time())
                diferencia = now - session_data["session_time"]
                if diferencia > 120:  #session time in seg
                    update_item_session(table_session_active,phone_number,now)
                    id = str(phone_number) + "_" + str(now)
                else:
                    id = str(phone_number) + "_" + str(session_data["session_time"])

            except:
                now = int(time.time())
                new_row = {"phone_number": phone_number, "session_time":now}
                save_item_ddb(table_session_active,new_row)
                
                id = str(phone_number) + "_" + str(now)

            try:
                print('REQUEST RECEIVED:', event)
                print('REQUEST CONTEXT:', context)
                print("PROMPT: ",text)

                #s = re.sub(r'[^a-zA-Z0-9]', '', query)

                tools = load_tools(
                        ["awslambda"],
                        awslambda_tool_name="search-passanger-information",
                        awslambda_tool_description="useful for searching passenger data by their identification number, send only the identification number in numbers and lowercase letters",
                        function_name=lambda_query_function_name,
                    )

                memory = memory_dynamodb(id,table_name_session)

                agent = langchain_agent(memory,tools,llm)

                agent.agent.llm_chain.prompt=promp_definition()
                response = agent(text)
                print(response)
                print(response['output'])


                whats_reply(phone, whats_token, phone_id, f"{response['output']}", keyvalue)

                end = int( time.time() )

                update_items_out(table,messsange_id,response['output'],end)
       
                return({"body":response['output']})
        
        
            except Exception as error: 
                print('FAILED!', error)
                return({"body":"Cuek! I dont know"})
            
        else:
            print("No text file")
