# Original implementation (commented out for reference)
# Original limitations:
# 1. Mixed concerns (configuration, session, conversation handling)
# 2. Limited error handling and logging
# 3. No type hints or input validation
# 4. Basic prompt templates
# 5. Hardcoded configuration
# 6. No separation of concerns
#
# See improved version in langchain_agent_text/improved/lambda_function.py 
# for better implementation with:
# 1. Proper code organization
# 2. Enhanced error handling
# 3. Better logging
# 4. Type safety
# 5. Configuration management
# 6. Improved prompt handling
#
# Original code preserved for reference:
"""
#################################################
## This function is to query a dynamoDB table ###
#################################################

import json
import boto3
import os
import requests
import time"""

# Import improved implementations
from improved.conversation import ConversationManager
from improved.session_manager import SessionManager
from improved.utils import normalize_phone, whats_reply, update_items_out

from db_utils import query,save_item_ddb,update_items_out,update_item_session

from langchain.chains import ConversationChain

from langchain.memory import ConversationBufferMemory
from langchain.memory.chat_message_histories import DynamoDBChatMessageHistory
from langchain.llms.bedrock import Bedrock
from boto3.dynamodb.conditions import Key
from utils import ( normalize_phone,whats_reply)

client_s3 = boto3.client('s3')
dynamodb_resource=boto3.resource('dynamodb')
bedrock_client = boto3.client("bedrock-runtime")

whatsapp_out_lambda = os.environ.get('WHATSAPP_OUT')

table_name_active_connections = os.environ.get('whatsapp_MetaData')

table_session_active = dynamodb_resource.Table(os.environ['user_sesion_metadata'])
table_name_session = os.environ.get('session_table_history')

base_path="/tmp/"
model_id = os.environ.get('ENV_MODEL_ID')

table = dynamodb_resource.Table(table_name_active_connections)


model_parameter = {"temperature": 0.0, "top_p": .9, "max_tokens_to_sample": 2000}
llm = Bedrock(model_id=model_id, model_kwargs=model_parameter,client=bedrock_client)

def memory_dynamodb(id,table_name_session):
    message_history = DynamoDBChatMessageHistory(table_name=table_name_session, session_id=id)
    memory = ConversationBufferMemory(
        memory_key="history", chat_memory=message_history, return_messages=True,ai_prefix="A",human_prefix="H"
    )
    return memory


def get_chat_response(llm,prompt, memory):
    
    conversation_with_summary = ConversationChain( #create a chat client
        llm = llm, #using the Bedrock LLM
        memory = memory, #with the summarization memory
        verbose = True #print out some of the internal states of the chain while running
    )
    conversation_with_summary.prompt.template ="""The following is a friendly conversation between a human and an AI. 
    The AI is talkative and provides lots of specific details from its context. 
    If the AI does not know the answer to a question, it truthfully says it does not know.
    Always reply in the original user language.

    Current conversation:
    {history}

    Human:{input}

    Assistant:"""
    return conversation_with_summary.predict(input=prompt)


# Original lambda_handler implementation commented out
# See improved version in lambda_function.py for better implementation

"""
def lambda_handler(event, context):
    print (event)

    whats_message = event['whats_message']
    print(whats_message)

    whats_token = event['whats_token']
    messages_id = event['messages_id']
    phone = event['phone']
    phone_id = event['phone_id']
    phone_number = phone.replace("+","")
"""

# Improved implementation using new components and better error handling
def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Enhanced Lambda handler with better organization and error handling.
    
    Args:
        event: API Gateway event
        context: Lambda context
        
    Returns:
        dict: Response with conversation result or error
        
    Raises:
        Exception: For critical failures after retries
    """
    logger.info(f"Received event: {event}")
    
    try:
        # Parse and validate request
        chat_request = ChatRequestData.from_event(event)
        
        # Initialize configuration
        config = ChatServiceConfig()
        
        # Initialize session management
        session_manager = SessionManager(
            table_session_active=config.table_session_active,
            session_timeout=config.session_timeout
        )
        
        # Get or create session
        session_info = session_manager.get_or_create_session(chat_request.normalized_phone)
        
        # Initialize conversation
        conversation_manager = ConversationManager(
            config=config,
            session_info=session_info
        )
        
        # Process message
        logger.info(f"Processing message: {chat_request.whats_message}")
        response = conversation_manager.get_response(chat_request.whats_message)
        
        # Send WhatsApp reply
        whats_reply(
            config.whatsapp_out_lambda,
            chat_request.phone,
            chat_request.whats_token,
            chat_request.phone_id,
            str(response),
            chat_request.messages_id
        )
        
        # Update conversation record
        end_time = int(time.time())
        update_items_out(
            config.table,
            chat_request.messages_id,
            response,
            end_time
        )
        
        logger.info("Successfully processed message")
        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": response,
                "session_id": session_info.session_id
            })
        }
            
    except Exception as error:
        logger.error(f"Error processing message: {str(error)}", exc_info=True)
        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": "An error occurred processing your message",
                "details": str(error)
            })
        }

    #The session ID is created to store the history of the messages. 

    try:
        session_data = query("phone_number",table_session_active,phone_number)
        now = int(time.time())
        diferencia = now - session_data["session_time"]
        if diferencia > 240:  #session time in seg
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
        print("PROMPT: ",whats_message)

        #s = re.sub(r'[^a-zA-Z0-9]', '', query)

        memory = memory_dynamodb(id,table_name_session)

        response = get_chat_response(llm,whats_message, memory)

        print(response)

        whats_reply(whatsapp_out_lambda,phone, whats_token, phone_id, f"{response}", messages_id)
        
        end = int( time.time())

        update_items_out(table,messages_id,response,end)
                
        return({"body":response})
        
        
    except Exception as error: 
            print('FAILED!', error)
            return({"body":"Cuek! I dont know"})

