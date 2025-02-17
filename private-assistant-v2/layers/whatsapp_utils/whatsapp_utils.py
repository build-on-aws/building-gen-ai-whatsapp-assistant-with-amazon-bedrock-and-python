import boto3
import json
import os
import boto3.dynamodb
import boto3.dynamodb.table


BUCKET_NAME = os.environ.get("BUCKET_NAME")
VOICE_PREFIX = os.environ.get("VOICE_PREFIX", "voice_")
IMAGE_PREFIX = os.environ.get("IMAGE_PREFIX", "image_")

class WhatsappMessage:
    def __init__(
        self,
        meta_phone_number,
        message,
        metadata={},
        client=None,
        meta_api_version="v20.0",
    ) -> None:
        # arn:aws:social-messaging:region:account:phone-number-id/976c72a700aac43eaf573ae050example
        self.meta_phone_number = meta_phone_number
        self.phone_number_arn = meta_phone_number.get("arn", "")
        # phone-number-id-976c72a700aac43eaf573ae050example
        self.phone_number_id = self.phone_number_arn.split(":")[-1].replace("/", "-")
        self.message = message
        self.metadata = metadata
        self.phone_number = message.get("from", "")
        self.meta_api_version = meta_api_version
        self.message_id = message.get("id", "")
        self.client = client if client else boto3.client("socialmessaging")

    def add_transcription(self, transcription):
        self.transcription = transcription
        self.message["audio"].update({"transcription": transcription})    

    def get_text(self):
        return self.message.get("text", {}).get("body", "")

    def get_media(self, message_type, download=True):
        """
        Retrieve media content from a WhatsApp message.
        
        Args:
            message_type (str): Type of media ('audio' or 'image')
            download (bool): Whether to download the media content
        
        Returns:
            dict: Media content information
        """
        # Get media metadata from message
        media_metadata = self.message.get(message_type)
        if not media_metadata:
            return {}
        
        if not download:
            return media_metadata

        # Map message types to their prefixes
        MEDIA_TYPE_PREFIXES = {
            "audio": VOICE_PREFIX,
            "image": IMAGE_PREFIX
        }
        
        media_prefix = MEDIA_TYPE_PREFIXES.get(message_type)
        if not media_prefix:
            raise ValueError(f"Unsupported media type: {message_type}")

        # Download media content
        media_content = self.download_media(
            media_id=media_metadata["id"],
            phone_id=self.phone_number_id,
            bucket_name=BUCKET_NAME,
            media_prefix=media_prefix
        )

        # Update media metadata with downloaded content
        if "ResponseMetadata" in media_content:
            del media_content["ResponseMetadata"]
        
        media_metadata.update(media_content)
        self.message[message_type] = media_metadata

        return media_metadata
    
    # https://docs.aws.amazon.com/social-messaging/latest/userguide/receive-message-image.html
    def download_media(self, media_id, phone_id, bucket_name, media_prefix):
        media_content = self.client.get_whatsapp_message_media(
            mediaId=media_id,
            originationPhoneNumberId=phone_id,
            destinationS3File={"bucketName": bucket_name, "key": media_prefix},
        )
        extension = media_content.get("mimeType","").split("/")[-1]
        # print("media content:", media_content)
        return dict(
            **media_content, location=f"s3://{bucket_name}/{media_prefix}{media_id}.{extension}"
        )

    def mark_as_read(self):
        message_object = {
            "messaging_product": "whatsapp",
            "message_id": self.message_id,
            "status": "read",
        }

        kwargs = dict(
            originationPhoneNumberId=self.phone_number_arn,
            metaApiVersion=self.meta_api_version,
            message=bytes(json.dumps(message_object), "utf-8"),
        )
        # print (kwargs)
        response = self.client.send_whatsapp_message(**kwargs)
        print("mark as read:", response)

    def reaction(self, emoji):
        message_object = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": f"+{self.phone_number}",
            "type": "reaction",
            "reaction": {"message_id": self.message_id, "emoji": emoji},
        }

        kwargs = dict(
            originationPhoneNumberId=self.phone_number_arn,
            metaApiVersion=self.meta_api_version,
            message=bytes(json.dumps(message_object), "utf-8"),
        )
        # print(kwargs)
        response = self.client.send_whatsapp_message(**kwargs)
        print("react to message:", response)

    def text_reply(self, text_message):
        print("reply message...")
        message_object = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "context": {"message_id": self.message_id},
            "to": f"+{self.phone_number}",
            "type": "text",
            "text": {"preview_url": False, "body": text_message},
        }

        kwargs = dict(
            originationPhoneNumberId=self.phone_number_id,
            metaApiVersion=self.meta_api_version,
            message=bytes(json.dumps(message_object), "utf-8"),
        )
        # print(kwargs)
        response = self.client.send_whatsapp_message(**kwargs)
        print("replied to message:", response)
        # message_object["id"] = response.get("messageId")
        # message_object["from"] = self.phone_number
        # replied_message = WhatsappMessage(self.meta_phone_number, message_object , self.metadata)
        # return replied_message

    def save(self, table):
        print("saving message...")
        table.put_item(Item=dict(**self.message, **self.metadata))


class WhatsappService:
    def __init__(self, sns_message) -> None:
        self.context = sns_message.get("context", {})
        self.meta_phone_number_ids = self.context.get("MetaPhoneNumberIds", [])
        self.meta_waba_ids = self.context.get("MetaWabaIds", [])
        self.webhook_entry = json.loads(sns_message.get("whatsAppWebhookEntry", {}))
        self.message_timestamp = sns_message.get("message_timestamp", "")
        self.changes = self.webhook_entry.get("changes", [])
        self.messages = []

        for change in self.changes:
            value = change.get("value", {})
            field = change.get("field", "")
            # print(f"field:{field}")
            if field == "messages":
                metadata = value.get("metadata", {})
                phone_number_id = metadata.get("phone_number_id", "")
                phone_number = self.get_phone_number_arn(phone_number_id)
                for message in value.get("messages", []):
                    print(f"message: {message}")
                    self.messages.append(
                        WhatsappMessage(phone_number, message, metadata)
                    )
            else:
                print(f"{value}")

    def get_phone_number_arn(self, phone_number_id):
        for phone_number in self.meta_phone_number_ids:
            if phone_number.get("metaPhoneNumberId") == phone_number_id:
                return phone_number