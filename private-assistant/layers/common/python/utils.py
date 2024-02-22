import boto3
import json
from botocore.exceptions import ClientError
secrets_client = boto3.client(service_name='secretsmanager')

lambda_client = boto3.client('lambda')

def get_config(secret_name):
    # Create a Secrets Manager client
    try:
        get_secret_value_response = secrets_client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        if e.response['Error']['Code'] == 'DecryptionFailureException':
            # Secrets Manager can't decrypt the protected secret text using the provided KMS key.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InternalServiceErrorException':
            # An error occurred on the server side.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InvalidParameterException':
            # You provided an invalid value for a parameter.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InvalidRequestException':
            # You provided a parameter value that is not valid for the current state of the resource.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'ResourceNotFoundException':
            # We can't find the resource that you asked for.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
    else:
        # Decrypts secret using the associated KMS CMK.
        # Depending on whether the secret is a string or binary, one of these fields will be populated.
        if 'SecretString' in get_secret_value_response:
            secret = get_secret_value_response['SecretString']
        else:
            secret = None
    return secret

def normalize_phone(phone):
    ### Country specific changes required on phone numbers
    
    ### Mexico specific, remove 1 after 52
    if(phone[0:2]=='52' and phone[2] == '1'):
        normalized = phone[0:2] + phone[3:]
    else:
        normalized  = phone
    return normalized
    ### End Mexico specific

def get_file_category(mimeType):
    ## Possible {AUDIO, CONTACTS, DOCUMENT, IMAGE, TEXT, TEMPLATE, VIDEO, STICKER, LOCATION, INTERACTIVE, REACTION}
    if('application' in mimeType): return 'document'
    elif('image' in mimeType): return 'image' 
    elif('audio' in mimeType): return 'audio'
    elif('video' in mimeType): return 'video'


def build_response(status_code, json_content):
        return {
        'statusCode': status_code,
        "headers": {
            "Content-Type": "text/html;charset=UTF-8",
            "charset": "UTF-8",
            "Access-Control-Allow-Origin": "*"
        },
        'body': json_content
    }

def validate_healthcheck(event, WHATS_VERIFICATION_TOKEN ):
    if('queryStringParameters' in event and 'hub.challenge' in event['queryStringParameters']):
        print(event['queryStringParameters'])
        print("Token challenge")
        if(event['queryStringParameters']['hub.verify_token'] == WHATS_VERIFICATION_TOKEN):
            print("Token verified")
            print(event['queryStringParameters']['hub.challenge'])
            response = event['queryStringParameters']['hub.challenge']
        else:
            response = ''
    else:
        print("Not challenge related")
        response = '<html><head></head><body> No key, no fun!</body></html>'
    return response

def whats_reply(whatsapp_out_lambda,phone, whats_token, phone_id, message, in_reply_to):

    print("WHATSAPP_OUT", in_reply_to, whats_token)

    try:       

        response_2 = lambda_client.invoke(
            FunctionName = whatsapp_out_lambda,
            InvocationType = 'Event' ,#'RequestResponse', 
            Payload = json.dumps({
                'phone': phone,
                'whats_token': whats_token,
                'phone_id': phone_id,
                'message': message,
                'in_reply_to': in_reply_to

            })
        )

        print(f'\nRespuesta:{response_2}')

        return response_2
    except ClientError as e:
        err = e.response
        error = err
        print(err.get("Error", {}).get("Code"))
        return f"Un error invocando {whatsapp_out_lambda}"