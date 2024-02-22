import aws_cdk as core
import aws_cdk.assertions as assertions

from private_assistant.private_assistant_stack import PrivateAssistantStack

# example tests. To run these tests, uncomment this file along with the example
# resource in private_assistant/private_assistant_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = PrivateAssistantStack(app, "private-assistant")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
