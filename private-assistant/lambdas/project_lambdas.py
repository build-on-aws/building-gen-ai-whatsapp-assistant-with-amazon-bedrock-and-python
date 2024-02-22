import sys

from aws_cdk import (
    Duration,
    aws_lambda,
    aws_ssm as ssm,
    Stack

)

from constructs import Construct


LAMBDA_TIMEOUT= 900

BASE_LAMBDA_CONFIG = dict (
    timeout=Duration.seconds(LAMBDA_TIMEOUT),       
    memory_size=256,
    tracing= aws_lambda.Tracing.ACTIVE)

COMMON_LAMBDA_CONF = dict (runtime=aws_lambda.Runtime.PYTHON_3_11, **BASE_LAMBDA_CONFIG)

from layers import Layers


class Lambdas(Construct):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        Lay = Layers(self, 'Lay')

        self.whatsapp_in = aws_lambda.Function(
            self, "whatsapp_in", handler="lambda_function.lambda_handler",
            description ="process WhatsApp incoming messages" ,
            code=aws_lambda.Code.from_asset("./lambdas/code/whatsapp_in"),
            layers= [Lay.bs4_requests, Lay.common],**COMMON_LAMBDA_CONF)
        
        self.whatsapp_out = aws_lambda.Function(
            self, "whatsapp_out", handler="lambda_function.lambda_handler",
            description ="Send WhatsApp message" ,
            code=aws_lambda.Code.from_asset("./lambdas/code/whatsapp_out"),
            layers= [Lay.bs4_requests, Lay.common],**COMMON_LAMBDA_CONF)

        self.audio_job_transcriptor = aws_lambda.Function(
            self, "audio_job_transcriptor", 
            description ="Start Transcribe Job  audio to text WhatsApp incoming messages" ,
            handler="lambda_function.lambda_handler",
            code=aws_lambda.Code.from_asset("./lambdas/code/audio_job_transcriptor"),
            layers= [Lay.bs4_requests, Lay.common],**COMMON_LAMBDA_CONF)
        
        self.transcriber_done = aws_lambda.Function(
            self, "transcriber_done", 
            description ="Read the text from transcriber job" ,
            handler="lambda_function.lambda_handler",
            code=aws_lambda.Code.from_asset("./lambdas/code/transcriber_done"),
            layers= [Lay.bs4_requests, Lay.common],**COMMON_LAMBDA_CONF)
    
        self.process_stream = aws_lambda.Function(
            self, "process_stream", 
            description ="Process Stream Lambda" ,
            handler="lambda_function.lambda_handler",
            code=aws_lambda.Code.from_asset("./lambdas/code/process_stream"),
            layers= [Lay.bs4_requests, Lay.common],**COMMON_LAMBDA_CONF)
        
        self.langchain_agent_text = aws_lambda.Function(
            self, "langChain_agent_text", 
            description ="Agent with LangChain and Amazon Bedrock" ,
            handler="lambda_function.lambda_handler",
            code=aws_lambda.Code.from_asset("./lambdas/code/langchain_agent_text"),
            layers= [Lay.bedrock,Lay.bs4_requests,Lay.common,Lay.langchain],
            architecture=aws_lambda.Architecture.ARM_64,
            **COMMON_LAMBDA_CONF)
        
        """
        self.langchain_agent_audio = aws_lambda.Function(
            self, "langChain_agent_audio", 
            description ="Airline Agent with LangChain and Amacon Bedrock" ,
            handler="lambda_function.lambda_handler",
            code=aws_lambda.Code.from_asset("./lambdas/code/langchain_agent_audio"),
            layers= [Lay.bedrock,Lay.bs4_requests,Lay.common,Lay.langchain],
            architecture=aws_lambda.Architecture.ARM_64,
            **COMMON_LAMBDA_CONF)
        """
