from aws_cdk import (
    RemovalPolicy,
    aws_dynamodb as ddb
)
from constructs import Construct


REMOVAL_POLICY = RemovalPolicy.DESTROY

TABLE_CONFIG = dict (removal_policy=REMOVAL_POLICY, billing_mode= ddb.BillingMode.PAY_PER_REQUEST)


class Tables(Construct):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.whatsapp_MetaData = ddb.Table(
            self, "whatsapp-MetaData", 
            partition_key=ddb.Attribute(name="messages_id", type=ddb.AttributeType.STRING),
            stream=ddb.StreamViewType.NEW_AND_OLD_IMAGES
        )

        #self.whatsapp_MetaData_follow = ddb.Table(
        #    self, "whatsapp-MetaData-follow", 
        #    partition_key=ddb.Attribute(name="messages_id", type=ddb.AttributeType.STRING),
        #    stream=ddb.StreamViewType.NEW_AND_OLD_IMAGES
        #)
                                      
        self.session_table_history = ddb.Table(
            self, "sessionTable", 
            partition_key=ddb.Attribute(name="SessionId", type=ddb.AttributeType.STRING),
            **TABLE_CONFIG)
        
        self.user_sesion_metadata = ddb.Table(
            self, "user_metadata", 
            partition_key=ddb.Attribute(name="phone_number", type=ddb.AttributeType.STRING),
            **TABLE_CONFIG)
        