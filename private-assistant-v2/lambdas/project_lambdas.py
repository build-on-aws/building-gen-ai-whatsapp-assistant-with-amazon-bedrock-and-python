import sys

from aws_cdk import (
    Duration,
    aws_lambda,
    aws_ssm as ssm,
    Stack

)

from constructs import Construct
from layers import Layers

LAMBDA_TIMEOUT= 900

BASE_LAMBDA_CONFIG = dict (
    timeout=Duration.seconds(LAMBDA_TIMEOUT),       
    memory_size=256,
    tracing= aws_lambda.Tracing.ACTIVE)

COMMON_LAMBDA_CONF = dict (runtime=aws_lambda.Runtime.PYTHON_3_11, **BASE_LAMBDA_CONFIG)



class Lambdas(Construct):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        Lay = Layers(self, 'Lay')

        self.whatsapp_in = aws_lambda.Function(
            self, "whatsapp_in", handler="lambda_function.lambda_handler",
            description ="process WhatsApp incoming messages" ,
            code=aws_lambda.Code.from_asset("./lambdas/code/whatsapp_in"),
            layers= [Lay.boto3layer],
            **COMMON_LAMBDA_CONF)
        
        
        self.transcriber_done = aws_lambda.Function(
            self, "transcriber_done", handler="lambda_function.lambda_handler",
            description ="job transcriber done" ,
            code=aws_lambda.Code.from_asset("./lambdas/code/transcriber_done"),
            **COMMON_LAMBDA_CONF)
    
        
        self.bedrock_agent = aws_lambda.Function(
            self, "bedrock_agent", handler="lambda_function.lambda_handler",
            description ="Invoke Amazon Bedrock Agent" ,
            code=aws_lambda.Code.from_asset("./lambdas/code/bedrock_agent"),
            layers= [Lay.boto3layer],
            **COMMON_LAMBDA_CONF)
        