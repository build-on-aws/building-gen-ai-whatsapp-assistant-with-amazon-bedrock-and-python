import boto3
import requests
from boto3.dynamodb.conditions import Key


def query_gd(key,table,keyvalue,Index_Name):
    resp = table.query(
    # Add the name of the index you want to use in your query.
    IndexName="jobnameindex",
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

def update_item(value,end,duration,table):
    try:
        response = table.update_item(
            Key={
                    "messages_id"  : value
                },
                UpdateExpression="set end=:newState, duration=:newState1",
                ExpressionAttributeValues={
                    ':newState': end,
                    ':newState1': duration,
                },
                ReturnValues="UPDATED_NEW")
        print (response)
    except Exception as e:
        print (e)
    else:
        return response
    
def save_item_ddb(table,item):
    response = table.put_item(Item=item)
    return response

def update_items_out(table,value,response_out,end_response):
    try:
        response = table.update_item(
            Key={
                    "messages_id" : value
                },
                UpdateExpression="set response_out=:item1, end_response=:item2",
                ExpressionAttributeValues={
                    ':item1': response_out,
                    ':item2': end_response,
                },
                ReturnValues="UPDATED_NEW")
        print (response)
    except Exception as e:
        print (e)
    else:
        return response
    
def update_item_session(table_name_session,value,session_time):
    try:
        response = table_name_session.update_item(
            Key={
                    "phone_number" : value
                },
                UpdateExpression="set session_time=:item1",
                ExpressionAttributeValues={
                    ':item1': session_time
                },
                ReturnValues="UPDATED_NEW")
        print (response)
    except Exception as e:
        print (e)
    else:
        return response

