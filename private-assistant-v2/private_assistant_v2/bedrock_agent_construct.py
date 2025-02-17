from aws_cdk import (
    aws_iam as iam,
    aws_lambda as _lambda,
    aws_bedrock as bedrock,
    Stack,
    CfnOutput,
    Duration
)
from constructs import Construct

class BedrockAgentConstruct(Construct):
    def __init__(self, scope: Construct, id: str, agent_name: str, model_id: str, **kwargs):
        super().__init__(scope, id)

        # Create the Bedrock agent
        self.agent = bedrock.CfnAgent(
            self, 'MultimodalAgent',
            agent_name=agent_name,
            agent_resource_role_arn=self._create_agent_role().role_arn,
            instruction='You are a helpful assistant that can process both text and images. When provided with an image, analyze its contents and provide relevant information.',
            foundation_model=model_id,
            idle_session_ttl_in_seconds=3600
        )

        # Create agent alias
        self.agent_alias = bedrock.CfnAgentAlias(
            self, 'AgentAlias',
            agent_id=self.agent.attr_agent_id,
            agent_alias_name='prod'
        )

    def _create_agent_role(self):
        # Create IAM role for the Bedrock agent
        role = iam.Role(
            self, 'BedrockAgentRole',
            assumed_by=iam.ServicePrincipal('bedrock.amazonaws.com')
        )

        # Add necessary permissions for image processing
        role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    'bedrock:InvokeModel',
                    's3:GetObject',
                    's3:PutObject',
                    'rekognition:DetectLabels',
                    'rekognition:DetectText'
                ],
                resources=['*']
            )
        )

        return role