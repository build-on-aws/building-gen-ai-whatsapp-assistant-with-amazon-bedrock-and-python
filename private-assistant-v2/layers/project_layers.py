import json
from constructs import Construct
from aws_cdk import aws_lambda



class Layers(Construct):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self._default_runtimes = [
            aws_lambda.Runtime.PYTHON_3_8,
            aws_lambda.Runtime.PYTHON_3_9,
            aws_lambda.Runtime.PYTHON_3_10,
            aws_lambda.Runtime.PYTHON_3_11
        ]

        # WhatsApp layer
        self.whatsapp = aws_lambda.LayerVersion(
            self, "whatsapp-layer", code=aws_lambda.Code.from_asset("./layers/whatsapp_utils/"),
            compatible_runtimes = self._default_runtimes, 
            description = 'whatsapp utils', layer_version_name = "whatsapp-layer"
        )

        # Transcribe layer
        self.transcribe = aws_lambda.LayerVersion(
            self, "transcribe-layer", code=aws_lambda.Code.from_asset("./layers/transcribe_utils/"),
            compatible_runtimes = self._default_runtimes, 
            description = 'transcribe utils', layer_version_name = "transcribe-layer"
        )


        # Boto3 layer for end user messaging
        self.boto3layer = aws_lambda.LayerVersion(
            self, "Boto3.1.35.69", code=aws_lambda.Code.from_asset("./layers/boto3.1.35.69.zip"),
            compatible_runtimes = self._default_runtimes, 
            description = 'Boto3 con Social Messaging', layer_version_name = "boto3-layer"
        )



    


