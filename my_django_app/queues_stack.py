from aws_cdk import (
    Stack,
    aws_sqs as sqs,
)
from constructs import Construct


class QueuesStack(Stack):

    def __init__(
            self,
            scope: Construct,
            construct_id: str,
            queue_name: str = "DefaultQueue",
            **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        # Create a SQS queue

        self.default_queue = sqs.Queue(
            self,
            "SQSQueue",
            queue_name=queue_name
        )

