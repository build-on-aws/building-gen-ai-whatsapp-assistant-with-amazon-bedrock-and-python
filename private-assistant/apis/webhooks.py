
from aws_cdk import (
    aws_apigateway as apg,
    Stack
)

from constructs import Construct



class WebhookApi(Construct):

    def __init__(self, scope: Construct, construct_id: str,lambdas, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        api = apg.RestApi(self, "myapi")
        api.root.add_cors_preflight(allow_origins=["*"], allow_methods=["GET", "POST"], allow_headers=["*"])

        cloudapi = api.root.add_resource("cloudapi",default_integration=apg.LambdaIntegration(lambdas.whatsapp_in, allow_test_invoke=False))

        cloudapi.add_method("GET") 
    
        cloudapi.add_method("POST") 
        