import os
from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_sqs as sqs,
    aws_ecs_patterns as ecs_patterns,
    aws_secretsmanager as secretsmanager,
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
            django_settings_module: str,
            sm_django_secret_name: str,
            sm_db_secret_name: str,  # Name of a secret in Secrets Manager containing database credentials
            sm_aws_api_key_id_secret_name: str,
            sm_aws_api_key_secret_secret_name: str,
            django_debug: bool = False,
            task_cpu: int = 256,
            task_memory_mib: int = 1024,
            task_min_scaling_capacity: int = 0,
            task_max_scaling_capacity: int = 4,
            scaling_steps=None,
            **kwargs
    ) -> None:
        self.vpc = vpc
        self.ecs_cluster = ecs_cluster
        self.queue = queue
        self.django_settings_module = django_settings_module.lower().strip()
        self.sm_django_secret_name = sm_django_secret_name
        self.sm_db_secret_name = sm_db_secret_name
        self.sm_aws_api_key_id_secret_name = sm_aws_api_key_id_secret_name
        self.sm_aws_api_key_secret_secret_name = sm_aws_api_key_secret_secret_name
        self.django_debug = django_debug
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

        # Prepare environment variables
        self.container_name = f"celery_worker"
        self.env_vars = {
            "DJANGO_SETTINGS_MODULE": self.django_settings_module,
            "DJANGO_DEBUG": str(self.django_debug),
            "AWS_SM_DB_SECRET_NAME": self.sm_db_secret_name,
            # Workaround to use VPC endpoints with SQS in Django
            # https://github.com/boto/boto3/issues/1900#issuecomment-873597264
            "AWS_DATA_PATH": "/home/web/botocore/",
            "AWS_ACCOUNT_ID": os.getenv('CDK_DEFAULT_ACCOUNT'),
            "AWS_SM_DJANGO_SECRET_NAME": sm_django_secret_name
        }

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
            secrets={
                "AWS_ACCESS_KEY_ID": ecs.Secret.from_secrets_manager(
                    secretsmanager.Secret.from_secret_name_v2(
                        self, f"AWSAccessKeyIDSecret",
                        secret_name=self.sm_aws_api_key_id_secret_name
                    )
                ),
                "AWS_SECRET_ACCESS_KEY": ecs.Secret.from_secrets_manager(
                    secretsmanager.Secret.from_secret_name_v2(
                        self, f"AWSAccessKeySecretSecret",
                        secret_name=self.sm_aws_api_key_secret_secret_name,
                    )
                ),
            }
        )
