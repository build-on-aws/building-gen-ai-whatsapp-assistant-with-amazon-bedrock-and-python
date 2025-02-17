from aws_cdk import (
    # Duration,
    Stack,
    aws_dynamodb as ddb,
    RemovalPolicy,
    aws_iam as iam,
    aws_bedrock as bedrock
)
from constructs import Construct

class CreateAgentWithKA(Construct):
    def __init__(self, scope: Construct, construct_id: str,agent_name,foundation_model, agent_instruction, description,agent_knowledge_base_property,agent_action_group_property,agent_resource_role, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)     

        self.agent_with_kb = bedrock.CfnAgent(self, "AgentWithKA",
                    agent_name=agent_name,
                    description=description,
                    auto_prepare = True,
                    idle_session_ttl_in_seconds = 600,
                    skip_resource_in_use_check_on_delete=False,
                    test_alias_tags={
                        "test_alias_tags_key": "AgentWithKA"
                    },
                    knowledge_bases = agent_knowledge_base_property,
                    action_groups = agent_action_group_property,
                    agent_resource_role_arn = self._create_agent_role().role_arn,
                    foundation_model=foundation_model,
                    instruction=agent_instruction,
                    )
        self.agent_with_kb.apply_removal_policy(RemovalPolicy.DESTROY)

        # Create agent alias
        self.agent_alias = bedrock.CfnAgentAlias(
            self, 'AgentAlias',
            agent_id=self.agent.attr_agent_id,
            agent_alias_name='prod',
            description=description,
            
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
                    'bedrock:*',
                    's3:GetObject',
                    's3:PutObject',
                    'rekognition:DetectLabels',
                    'rekognition:DetectText'
                ],
                resources=['*']
            )
        )

        return role
        
class CreateAgentSimple(Construct):
    def create_agent_role(self):
        # Create IAM role for the Bedrock agent
        role = iam.Role(
            self, 'BedrockAgentSimpleRole',
            assumed_by=iam.ServicePrincipal('bedrock.amazonaws.com')
        )

        # Add necessary permissions for image processing
        role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    'bedrock:*',
                    's3:GetObject',
                    's3:PutObject',
                    'rekognition:DetectLabels',
                    'rekognition:DetectText'
                ],
                resources=['*']
            )
        )

        return role

    def __init__(self, scope: Construct, id: str, agent_name,foundation_model, agent_instruction, description, **kwargs):
        super().__init__(scope, id)    

        # Create the Bedrock agent
        self.agent = bedrock.CfnAgent(
            self, 'CreateAgentSimple',
            agent_name=agent_name,
            description=description,
            auto_prepare = True,
            agent_resource_role_arn=self.create_agent_role().role_arn,
            instruction=agent_instruction,
            foundation_model=foundation_model,
            idle_session_ttl_in_seconds=3600,
            test_alias_tags={
                        "test_alias_tags_key": "CreateAgentSimple"
                    },
            
        )

        # Create agent alias
        self.agent_alias = bedrock.CfnAgentAlias(
            self, 'AgentAlias',
            agent_id=self.agent.attr_agent_id,
            agent_alias_name='prod',
            description=description,
        )

        self.agent.apply_removal_policy(RemovalPolicy.DESTROY)


    def create_agent_role(self):
        # Create IAM role for the Bedrock agent
        role = iam.Role(
            self, 'BedrockAgentSimpleRole',
            assumed_by=iam.ServicePrincipal('bedrock.amazonaws.com')
        )

        # Add necessary permissions for image processing
        role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    'bedrock:*',
                    's3:GetObject',
                    's3:PutObject',
                    'rekognition:DetectLabels',
                    'rekognition:DetectText'
                ],
                # amazonq-ignore-next-line
                resources=['*']
            )
        )

        return role

        

        

