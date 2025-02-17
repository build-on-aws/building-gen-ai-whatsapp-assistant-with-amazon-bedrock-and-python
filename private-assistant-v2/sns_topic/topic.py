from aws_cdk import aws_sns as sns, aws_ssm as ssm, aws_sns_subscriptions as subs

from constructs import Construct


class Topic(Construct):

    def __init__(
        self, scope: Construct, construct_id: str, notification_email=None, lambda_function=None, **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.topic = sns.Topic(self, "Topic")

        if lambda_function:
            self.topic.add_subscription(subs.LambdaSubscription(lambda_function))


    def add_lambda_subscription(self, lambda_function):
        self.topic.add_subscription(subs.LambdaSubscription(lambda_function))