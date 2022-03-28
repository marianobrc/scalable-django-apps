from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_sqs as sqs,
    aws_ecs_patterns as ecs_patterns,
)
from constructs import Construct


class BackendWorkersStack(Stack):

    def __init__(
            self,
            scope: Construct,
            construct_id: str,
            vpc: ec2.Vpc,
            ecs_cluster: ecs.Cluster,
            queue: sqs.Queue,
            env_vars: dict,
            secrets: dict,
            task_cpu: int = 256,
            task_memory_mib: int = 1024,
            task_min_scaling_capacity: int = 0,
            task_max_scaling_capacity: int = 4,
            scaling_steps: list = None,
            **kwargs
    ) -> None:
        self.vpc = vpc
        self.ecs_cluster = ecs_cluster
        self.queue = queue
        self.env_vars = env_vars
        self.secrets = secrets
        self.task_cpu = task_cpu
        self.task_memory_mib = task_memory_mib
        self.task_min_scaling_capacity = task_min_scaling_capacity
        self.task_max_scaling_capacity = task_max_scaling_capacity
        if scaling_steps:
            self.scaling_steps = scaling_steps
        else:
            self.scaling_steps = [
                {"upper": 0, "change": -1},    # 0 msgs = 0 workers
                {"lower": 1, "change": +1},    # 1 msg = 1 worker
                {"lower": 100, "change": +1},  # 100 msgs = 2 workers
                {"lower": 200, "change": +2},  # 200 msgs = 4 workers
            ]
        super().__init__(scope, construct_id, **kwargs)

        if not self.ecs_cluster:
            self.ecs_cluster = ecs.Cluster(self, f"WorkersCluster", vpc=vpc)

        # Instantiate the worker
        self.container_name = f"celery_worker"
        self.workers_fargate_service = ecs_patterns.QueueProcessingFargateService(
            self,
            f"CeleryWorkers",
            queue=queue,
            platform_version=ecs.FargatePlatformVersion.VERSION1_4,
            cluster=self.ecs_cluster,  # Required
            cpu=task_cpu,  # Default is 256
            memory_limit_mib=task_memory_mib,  # Default is 512
            min_scaling_capacity=self.task_min_scaling_capacity,
            max_scaling_capacity=self.task_max_scaling_capacity,
            scaling_steps=self.scaling_steps,
            image=ecs.ContainerImage.from_asset(
                directory="app/",
                file="docker/app/Dockerfile",
                target="prod"
            ),
            container_name=self.container_name,
            command=["start-celery-worker.sh", queue.queue_name],
            environment=self.env_vars,
            secrets=self.secrets
        )
