import aws_cdk as core
import aws_cdk.assertions as assertions

from private_assistant_v2.private_assistant_v2_stack import PrivateAssistantV2Stack

# example tests. To run these tests, uncomment this file along with the example
# resource in private_assistant_v2/private_assistant_v2_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = PrivateAssistantV2Stack(app, "private-assistant-v2")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
