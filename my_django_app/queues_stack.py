from aws_cdk import (
    Stack,
    aws_sqs as sqs,
    aws_ssm as ssm,
)
from constructs import Construct


class QueuesStack(Stack):

    def __init__(
            self,
            scope: Construct,
            construct_id: str,
            **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        # Create a SQS queue

        self.default_queue = sqs.Queue(
            self,
            "SQSQueue"
        )
        self.celery_broker_url = ssm.StringParameter(
            self,
            "CeleryBrokerUrlParam",
            parameter_name=f"/{scope.stage_name}/CeleryBrokerUrlParam",
            string_value=self.default_queue.queue_url
        )
