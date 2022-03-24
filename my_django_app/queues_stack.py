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
        # Save the queue url in SSM Parameter Store
        self.default_queue_url_param = ssm.StringParameter(
            self,
            "SqsDefaultQueueUrlParam",
            parameter_name=f"/{scope.stage_name}/SqsDefaultQueueUrlParam",
            string_value=self.default_queue.queue_url
        )
