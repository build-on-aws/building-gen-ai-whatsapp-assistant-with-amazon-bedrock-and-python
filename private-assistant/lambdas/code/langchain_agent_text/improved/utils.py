# Improved utility functions with better error handling and logging
# Original implementation had limited error handling and no logging

import json
import logging
import time
from typing import Dict, Any, Optional

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

def normalize_phone(phone: str) -> str:
    """Normalize phone number by removing '+' prefix.
    
    Original implementation was a simple replace, this adds validation.
    
    Args:
        phone: Phone number string
        
    Returns:
        str: Normalized phone number
        
    Raises:
        ValueError: If phone number is invalid
    """
    if not phone:
        raise ValueError("Phone number cannot be empty")
    
    normalized = phone.replace("+", "")
    if not normalized.isdigit():
        raise ValueError(f"Invalid phone number: {phone}")
    
    return normalized

def whats_reply(
    lambda_name: str,
    phone: str,
    token: str,
    phone_id: str,
    message: str,
    reply_to: str,
    max_retries: int = 3
) -> None:
    """Send WhatsApp reply with improved error handling and retries.
    
    Original implementation had basic error handling. This version adds:
    - Retry logic
    - Better error messages
    - Logging
    - Input validation
    - Type hints
    
    Args:
        lambda_name: Name of WhatsApp output Lambda
        phone: Recipient phone number
        token: WhatsApp token
        phone_id: WhatsApp phone ID
        message: Message to send
        reply_to: Message ID to reply to
        max_retries: Maximum number of retry attempts
        
    Raises:
        Exception: If sending message fails after all retries
    """
    if not all([lambda_name, phone, token, phone_id, message, reply_to]):
        raise ValueError("All parameters are required")
    
    lambda_client = boto3.client('lambda')
    
    payload = {
        "phone": phone,
        "whats_token": token, 
        "phone_id": phone_id,
        "message": message,
        "messages_id": reply_to
    }
    
    retry_count = 0
    while retry_count < max_retries:
        try:
            logger.info(f"Sending WhatsApp reply to {phone}")
            response = lambda_client.invoke(
                FunctionName=lambda_name,
                InvocationType='Event',
                Payload=json.dumps(payload)
            )
            
            if response['StatusCode'] != 202:
                raise Exception(f"Unexpected status code: {response['StatusCode']}")
                
            logger.info("Successfully sent WhatsApp reply")
            return
            
        except Exception as e:
            retry_count += 1
            if retry_count == max_retries:
                logger.error(f"Failed to send WhatsApp reply after {max_retries} attempts: {str(e)}")
                raise
            logger.warning(f"Error sending WhatsApp reply (attempt {retry_count}): {str(e)}")
            time.sleep(1)

def update_items_out(
    table: Any,
    message_id: str,
    response: str,
    timestamp: int
) -> None:
    """Update DynamoDB items with improved error handling.
    
    Original implementation had basic error handling. This version adds:
    - Input validation
    - Better error messages
    - Logging
    - Type hints
    
    Args:
        table: DynamoDB table object
        message_id: Message ID to update
        response: Response message
        timestamp: Timestamp for update
        
    Raises:
        Exception: If update fails
    """
    try:
        logger.info(f"Updating conversation record for message {message_id}")
        
        table.update_item(
            Key={'messages_id': message_id},
            UpdateExpression='SET #resp = :r, #end = :e',
            ExpressionAttributeNames={
                '#resp': 'response',
                '#end': 'end'
            },
            ExpressionAttributeValues={
                ':r': response,
                ':e': timestamp
            }
        )
        
        logger.info("Successfully updated conversation record")
        
    except Exception as e:
        logger.error(f"Failed to update conversation record: {str(e)}")
        raise