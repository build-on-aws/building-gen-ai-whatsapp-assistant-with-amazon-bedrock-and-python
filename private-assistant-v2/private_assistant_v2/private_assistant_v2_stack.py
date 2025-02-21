from aws_cdk import (
    # Duration,
    Stack,
    CfnOutput,
    aws_iam as iam,
    aws_s3 as s3,
    RemovalPolicy,
    aws_dynamodb as ddb,
    aws_s3_notifications,
    aws_s3_deployment as s3deploy # Add this import
    # aws_sqs as sqs,
)
from constructs import Construct

from sns_topic import Topic
from lambdas import Lambdas
from databases import Tables
from agent_bedrock import CreateAgentSimple
import json


model_id = 'amazon.nova-pro-v1:0'
model_id_multimodal = "us.amazon.nova-pro-v1:0"
agent_name = 'DemoMultimodalAssistant'
#    "foundation_model": "anthropic.claude-3-5-sonnet-20240620-v1:0"
file_path_agent_data = './private_assistant_v2/agent_data.json'

class PrivateAssistantV2Stack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        stk = Stack.of(self)
        region = stk.region
        account_id = stk.account

        with open(file_path_agent_data, 'r') as file:
            agent_data = json.load(file)
        
        agent_simple = CreateAgentSimple(self, "agentsimple", agent_name, model_id, agent_data["agent_instruction"], agent_data["description"])    

        agent_id = agent_simple.agent.attr_agent_id
        agent_alias_id = agent_simple.agent_alias.attr_agent_alias_id

        #https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_bedrock/CfnAgentAlias.html

        Fn = Lambdas(self, "L")

        # amazonq-ignore-next-line
        Bucket = s3.Bucket(self, "S3", removal_policy=RemovalPolicy.DESTROY)
        Bucket.grant_read_write(Fn.whatsapp_in)
        Bucket.grant_read_write(Fn.bedrock_agent)
        Bucket.grant_read_write(Fn.transcriber_done)

        # Create empty folders (prefixes) in the bucket
        s3deploy.BucketDeployment(self, "CreateFolders",
        sources=[s3deploy.Source.data("voice/placeholder.txt", "")], # Creates voice_ folder
        destination_bucket=Bucket,
        retain_on_delete=False,
        )

        s3deploy.BucketDeployment(self, "CreateImageFolder",
        sources=[s3deploy.Source.data("image/placeholder.txt", "")], # Creates image_ folder
        destination_bucket=Bucket,
        retain_on_delete=False,
        )

        s3deploy.BucketDeployment(self, "CreateTranscribeFolder",
        sources=[s3deploy.Source.data("transcribe_response/placeholder.txt", "")], # Creates image_ folder
        destination_bucket=Bucket,
        retain_on_delete=False,
        )

        s3deploy.BucketDeployment(self, "CreateVideoFolder",
        sources=[s3deploy.Source.data("video/placeholder.txt", "")], # Creates image_ folder
        destination_bucket=Bucket,
        retain_on_delete=False,
        )

        s3deploy.BucketDeployment(self, "CreateDocumentFolder",
        sources=[s3deploy.Source.data("document/placeholder.txt", "")], # Creates image_ folder
        destination_bucket=Bucket,
        retain_on_delete=False,
        )

        Bucket.add_event_notification(s3.EventType.OBJECT_CREATED,
                                              aws_s3_notifications.LambdaDestination(Fn.transcriber_done),
                                              s3.NotificationKeyFilter(prefix="transcribe_response/"))

        Tb = Tables(self, "Table")
        Tb.messages.grant_read_write_data(Fn.whatsapp_in)
        Tb.agenthistory.grant_read_write_data(Fn.bedrock_agent)
        Tb.messages.grant_read_write_data(Fn.transcriber_done)

        Tb.messages.add_global_secondary_index(index_name = 'jobnameindex', 
                                                            partition_key = ddb.Attribute(name="jobName",type=ddb.AttributeType.STRING), 
                                                            projection_type=ddb.ProjectionType.KEYS_ONLY)

        Tp = Topic(self, "WhatsappEventsDestination", lambda_function=Fn.whatsapp_in)

        Tp.topic.add_to_resource_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                principals=[iam.ServicePrincipal("social-messaging.amazonaws.com")],
                actions=["sns:Publish"],
                resources=[Tp.topic.topic_arn]
            )
        )

        # Grant permissions for WhatsApp messaging
        Fn.whatsapp_in.add_to_role_policy(
            iam.PolicyStatement(
                actions=["social-messaging:SendWhatsAppMessage", "social-messaging:GetWhatsAppMessageMedia"],
                resources=[f"arn:aws:social-messaging:{region}:{account_id}:phone-number-id/*"]
            )
        )

        # Grant permissions for WhatsApp messaging
        Fn.bedrock_agent.add_to_role_policy(
            iam.PolicyStatement(
                actions=["social-messaging:SendWhatsAppMessage", "social-messaging:GetWhatsAppMessageMedia"],
                resources=[f"arn:aws:social-messaging:{region}:{account_id}:phone-number-id/*"]
            )
        )

        # Grant permissions for Bedrock agent interaction
        Fn.whatsapp_in.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    'bedrock:InvokeAgent',
                    'bedrock:InvokeModel',
                    'bedrock-agent-runtime:InvokeAgent'
                ],
                resources=['*']
            )
        )
        
        # Add environment variables for the Bedrock agent
        Fn.whatsapp_in.add_to_role_policy(
            iam.PolicyStatement(
                actions=["transcribe:*"],
                resources=["*"]
            )
        )
        
        Fn.whatsapp_in.add_environment("TABLE_NAME", Tb.messages.table_name)
        Fn.whatsapp_in.add_environment("BUCKET_NAME", Bucket.bucket_name)
        Fn.whatsapp_in.add_environment("VOICE_PREFIX", "voice/voice_")
        Fn.whatsapp_in.add_environment("IMAGE_PREFIX", "image/image_")
        Fn.whatsapp_in.add_environment("VIDEO_PREFIX", "video/video_")
        Fn.whatsapp_in.add_environment("DOC_PREFIX", "document/document_")
        Fn.whatsapp_in.add_environment("ENV_TRANSCRIBE_PREFIX", "transcribe_response")
        Fn.bedrock_agent.grant_invoke(Fn.whatsapp_in)


        Fn.whatsapp_in.add_environment( key='ENV_LAMBDA_BEDROCK_AGENT', value=Fn.bedrock_agent.function_name)
        #Fn.whatsapp_in.add_environment( key='ENV_TRANSCRIBE_PREFIX', value=Fn.transcriber_done.function_name)

        Fn.bedrock_agent.add_to_role_policy(iam.PolicyStatement( actions=["bedrock:*"], resources=['*']))
        Fn.bedrock_agent.add_environment("ENV_AGENT_ID", agent_id)
        Fn.bedrock_agent.add_environment("BUCKET_NAME", Bucket.bucket_name)
        Fn.bedrock_agent.add_environment("ENV_ALIAS_ID", agent_alias_id)
        Fn.bedrock_agent.add_environment("ENV_MODEL_ID", model_id_multimodal)
        Fn.bedrock_agent.add_environment("TABLE_NAME", Tb.agenthistory.table_name)
        Fn.bedrock_agent.add_environment(key='ENV_KEY_NAME', value="phone_number") 

    
        Fn.transcriber_done.add_to_role_policy(iam.PolicyStatement( actions=["dynamodb:*"], resources=[f"{Tb.messages.table_arn}",f"{Tb.messages.table_arn}/*"]))
        Fn.transcriber_done.add_environment(key='ENV_INDEX_NAME', value="jobnameindex")
        Fn.transcriber_done.add_environment(key='ENV_KEY_NAME', value="id") 
        Fn.transcriber_done.add_environment("TABLE_NAME", Tb.messages.table_name)
        Fn.transcriber_done.add_environment( key='ENV_LAMBDA_BEDROCK_AGENT', value=Fn.bedrock_agent.function_name)

        Fn.bedrock_agent.grant_invoke(Fn.transcriber_done)

    
        CfnOutput(self, "TopicArn", value=Tp.topic.topic_arn)
