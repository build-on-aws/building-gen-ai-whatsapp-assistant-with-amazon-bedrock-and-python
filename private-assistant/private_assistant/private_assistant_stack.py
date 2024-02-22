from aws_cdk import (
    # Duration,
    Stack,SecretValue,
    # aws_sqs as sqs,
    RemovalPolicy,
    aws_dynamodb as ddb,
    aws_secretsmanager as secretsmanager,
    aws_iam as iam,
    aws_s3_notifications,
    aws_s3 as s3,
    aws_lambda,
    aws_lambda_event_sources
)
from constructs import Construct
from lambdas import Lambdas
from apis import WebhookApi
from databases import Tables
from s3_cloudfront import S3Deploy

class PrivateAssistantStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        LANGUAGE_CODE = 'es-US'

        REMOVAL_POLICY = RemovalPolicy.DESTROY
        TABLE_CONFIG = dict (removal_policy=REMOVAL_POLICY, billing_mode= ddb.BillingMode.PAY_PER_REQUEST)
        AudioKeyName = "audio-from-whatsapp"
        TextBucketName = "text-to-whatsapp"
        model_id = "anthropic.claude-instant-v1"
        
        DISPLAY_PHONE_NUMBER = 'YOU-NUMBER'

   

        #Whatsapp Secrets Values
        secrets = secretsmanager.Secret(self, "Secrets", secret_object_value = {
            'WHATS_TOKEN': SecretValue.unsafe_plain_text('FROM_WHATSAPP'),
            'WHATS_VERIFICATION_TOKEN': SecretValue.unsafe_plain_text('CREATE_ONE'),
            'WHATS_PHONE_ID':SecretValue.unsafe_plain_text('FROM_WHATSAPP'),
            'WHATS_TOKEN': SecretValue.unsafe_plain_text('FROM_WHATSAPP')
           }) 
        
        Tbl = Tables(self, 'Tbl')

        Tbl.whatsapp_MetaData.add_global_secondary_index(index_name = 'jobnameindex', 
                                                            partition_key = ddb.Attribute(name="jobName",type=ddb.AttributeType.STRING), 
                                                            projection_type=ddb.ProjectionType.KEYS_ONLY)


        s3_deploy = S3Deploy(self, "The-transcriber", TextBucketName,TextBucketName)

        #Create Amazon Lambda Functions
        Fn  = Lambdas(self,'Fn')
        #Create Amazon API Gateweay

        Api = WebhookApi(self, "API", lambdas=Fn)

         # Amazon Lambda Function whatsapp_in - Config

        Fn.whatsapp_in.add_environment(key='CONFIG_PARAMETER', value=secrets.secret_arn)
        secrets.grant_read(Fn.whatsapp_in)

        Fn.whatsapp_in.add_environment(key='REFRESH_SECRETS', value='false')
        Fn.whatsapp_in.add_environment(key='DISPLAY_PHONE_NUMBER', value= DISPLAY_PHONE_NUMBER)

        Tbl.whatsapp_MetaData.grant_full_access(Fn.whatsapp_in)

        Fn.whatsapp_in.add_environment(key='whatsapp_MetaData', value=Tbl.whatsapp_MetaData.table_name)

        #Fn.whatsapp_in.add_environment(key='whatsapp_MetaData_follow', value=Tbl.whatsapp_MetaData_follow.table_name)
        #Tbl.whatsapp_MetaData_follow.grant_full_access(Fn.whatsapp_in)
        
        Fn.process_stream.add_environment( key='ENV_LAMBDA_AGENT_TEXT', value=Fn.langchain_agent_text.function_name )
        Fn.process_stream.add_environment( key='JOB_TRANSCRIPTOR_LAMBDA', value=Fn.audio_job_transcriptor.function_name )
        Fn.process_stream.add_environment(key='whatsapp_MetaData', value=Tbl.whatsapp_MetaData.table_name)
        
        
        Fn.process_stream.add_event_source(
            aws_lambda_event_sources.DynamoEventSource(table=Tbl.whatsapp_MetaData,
            starting_position=aws_lambda.StartingPosition.TRIM_HORIZON))
        Tbl.whatsapp_MetaData.grant_full_access(Fn.process_stream)
        

        # Amazon Lambda Function whatsapp_out - Config
        
        Fn.whatsapp_out.add_environment(key='ENV_INDEX_NAME', value="jobnameindex")
        Fn.whatsapp_out.add_environment(key='ENV_KEY_NAME', value="messages_id")

        Fn.whatsapp_out.grant_invoke(Fn.langchain_agent_text)

        
        # Amazon Lambda Function audio_job_transcriptor - Config

        Fn.audio_job_transcriptor.add_to_role_policy(iam.PolicyStatement( actions=["transcribe:*"], resources=['*']))
        Fn.audio_job_transcriptor.add_environment(key='BucketName', value=s3_deploy.bucket.bucket_name)
        Fn.audio_job_transcriptor.add_environment(key='whatsapp_MetaData', value=Tbl.whatsapp_MetaData.table_name)
        Fn.audio_job_transcriptor.add_environment(key='AudioKeyName', value=AudioKeyName)
        Fn.audio_job_transcriptor.add_environment(key='TextBucketName', value=TextBucketName)
        Fn.audio_job_transcriptor.grant_invoke(Fn.process_stream)
        Fn.audio_job_transcriptor.add_to_role_policy(iam.PolicyStatement( actions=["dynamodb:*"], resources=[f"{Tbl.whatsapp_MetaData.table_arn}",f"{Tbl.whatsapp_MetaData.table_arn}/*"]))
        Fn.audio_job_transcriptor.add_environment(key='ENV_INDEX_NAME', value="jobnameindex")
        Fn.audio_job_transcriptor.add_environment(key='ENV_KEY_NAME', value="messages_id")  

        s3_deploy.bucket.grant_read_write(Fn.audio_job_transcriptor) 
        Tbl.whatsapp_MetaData.grant_full_access(Fn.audio_job_transcriptor) 

        # Amazon Lambda Function audio_job_transcriptor done - Config

        s3_deploy.bucket.grant_read(Fn.transcriber_done)

        s3_deploy.bucket.add_event_notification(s3.EventType.OBJECT_CREATED,
                                              aws_s3_notifications.LambdaDestination(Fn.transcriber_done),
                                              s3.NotificationKeyFilter(prefix=TextBucketName+"/"))
        
        Fn.transcriber_done.add_environment( key='WHATSAPP_OUT', value=Fn.whatsapp_out.function_name )
        Fn.transcriber_done.add_to_role_policy(iam.PolicyStatement( actions=["dynamodb:*"], resources=[f"{Tbl.whatsapp_MetaData.table_arn}",f"{Tbl.whatsapp_MetaData.table_arn}/*"]))
        Fn.transcriber_done.add_environment(key='ENV_INDEX_NAME', value="jobnameindex")
        Fn.transcriber_done.add_environment(key='ENV_KEY_NAME', value="messages_id")        

        Fn.whatsapp_out.grant_invoke(Fn.transcriber_done)

        Tbl.whatsapp_MetaData.grant_full_access(Fn.transcriber_done)
        Fn.transcriber_done.add_environment(key='whatsapp_MetaData', value=Tbl.whatsapp_MetaData.table_name)

        Fn.langchain_agent_text.grant_invoke(Fn.transcriber_done)

        Fn.transcriber_done.add_environment( key='ENV_LAMBDA_AGENT_TEXT', value=Fn.langchain_agent_text.function_name)

        # langchain_agent_text

        Tbl.session_table_history.grant_full_access(Fn.langchain_agent_text)
        Fn.langchain_agent_text.add_environment(key='session_table_history', value=Tbl.session_table_history.table_name)

        Tbl.whatsapp_MetaData.grant_full_access(Fn.langchain_agent_text)
        Fn.langchain_agent_text.add_environment(key='whatsapp_MetaData', value=Tbl.whatsapp_MetaData.table_name)

        Tbl.user_sesion_metadata.grant_full_access(Fn.langchain_agent_text)
        Fn.langchain_agent_text.add_environment(key='user_sesion_metadata', value=Tbl.user_sesion_metadata.table_name)
        
        Fn.langchain_agent_text.add_environment(key='ENV_MODEL_ID', value=model_id)

        Fn.langchain_agent_text.add_environment( key='WHATSAPP_OUT', value=Fn.whatsapp_out.function_name )
        
        Fn.langchain_agent_text.grant_invoke(Fn.process_stream)
        Fn.langchain_agent_text.add_to_role_policy(iam.PolicyStatement( actions=["bedrock:*"], resources=['*']))

        

