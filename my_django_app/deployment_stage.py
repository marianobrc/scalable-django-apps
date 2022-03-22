import os
import typing
from constructs import Construct
from aws_cdk import (
    Stage,
    Environment,
    aws_rds as rds,
)
from my_django_app.network_stack import NetworkStack
from my_django_app.database_stack import DatabaseStack
from my_django_app.my_django_app_stack import MyDjangoAppStack
from my_django_app.static_files_stack import StaticFilesStack
from my_django_app.queues_stack import QueuesStack
from my_django_app.backend_workers_stack import BackendWorkersStack
from my_django_app.variables_stack import VariablesStack
from my_django_app.dns_route_to_alb_stack import DnsRouteToAlbStack


class MyDjangoAppPipelineStage(Stage):

    def __init__(
            self,
            scope: Construct,
            id: str,
            django_settings_module: str,
            django_debug: bool,
            domain_name: str,
            subdomain: str = None,
            db_min_capacity: rds.AuroraCapacityUnit = rds.AuroraCapacityUnit.ACU_2,
            db_max_capacity: rds.AuroraCapacityUnit = rds.AuroraCapacityUnit.ACU_4,
            db_auto_pause_minutes: int = 0,
            app_task_min_scaling_capacity: int = 2,
            app_task_max_scaling_capacity: int = 4,
            worker_task_min_scaling_capacity: int = 1,
            worker_task_max_scaling_capacity: int = 4,
            worker_scaling_steps: list = None,
            **kwargs
    ):

        super().__init__(scope, id, **kwargs)
        self.django_settings_module = django_settings_module
        self.django_debug = django_debug
        self.domain_name = domain_name
        self.subdomain = subdomain
        self.db_min_capacity = db_min_capacity
        self.db_max_capacity = db_max_capacity
        self.db_auto_pause_minutes = db_auto_pause_minutes
        self.app_task_min_scaling_capacity = app_task_min_scaling_capacity
        self.app_task_max_scaling_capacity = app_task_max_scaling_capacity
        self.worker_task_min_scaling_capacity = worker_task_min_scaling_capacity
        self.worker_task_max_scaling_capacity = worker_task_max_scaling_capacity
        self.worker_scaling_steps = worker_scaling_steps

        self.network = NetworkStack(
            self,
            "Network",
            env=Environment(
                account=os.getenv('CDK_DEFAULT_ACCOUNT'),
                region=os.getenv('CDK_DEFAULT_REGION')
            ),
        )
        self.database = DatabaseStack(
            self,
            "Database",
            env=Environment(
                account=os.getenv('CDK_DEFAULT_ACCOUNT'),
                region=os.getenv('CDK_DEFAULT_REGION')
            ),
            vpc=self.network.vpc,
            database_name="app_db",
            min_capacity=self.db_min_capacity,
            max_capacity=self.db_max_capacity,
            auto_pause_minutes=self.db_auto_pause_minutes
        )
        # Serve static files for the Backoffice (django-admin)
        self.static_files = StaticFilesStack(
            self,
            "StaticFiles",
            env=Environment(
                account=os.getenv('CDK_DEFAULT_ACCOUNT'),
                region=os.getenv('CDK_DEFAULT_REGION')
            ),
            cors_allowed_origins=[
                f"https://{self.subdomain}.{self.domain_name}" if self.subdomain else f"https://{self.domain_name}"
            ]
        )
        self.queues = QueuesStack(
            self,
            "Queues",
            env=Environment(
                account=os.getenv('CDK_DEFAULT_ACCOUNT'),
                region=os.getenv('CDK_DEFAULT_REGION')
            ),
        )
        self.app_env_vars = {
            "DJANGO_SETTINGS_MODULE": self.django_settings_module,
            "DJANGO_DEBUG": str(self.django_debug),
            # Workaround to use VPC endpoints with SQS in Django
            # https://github.com/boto/boto3/issues/1900#issuecomment-873597264
            "AWS_DATA_PATH": "/home/web/botocore/",
            "AWS_ACCOUNT_ID": os.getenv('CDK_DEFAULT_ACCOUNT'),
            "AWS_STATIC_FILES_BUCKET_NAME":  self.static_files.s3_bucket.bucket_name,
            "AWS_STATIC_FILES_CLOUDFRONT_URL": self.static_files.cloudfront_distro.distribution_domain_name,
            "CELERY_BROKER_URL": self.queues.default_queue.queue_url,
            "CELERY_TASK_ALWAYS_EAGER": "False"
        }
        self.variables = VariablesStack(
            self,
            "AppVariables",
            env=Environment(
                account=os.getenv('CDK_DEFAULT_ACCOUNT'),
                region=os.getenv('CDK_DEFAULT_REGION')
            ),
            database_secrets=self.database.aurora_serverless_db.secret,
        )
        self.django_app = MyDjangoAppStack(
            self,
            "AppService",
            env=Environment(
                account=os.getenv('CDK_DEFAULT_ACCOUNT'),
                region=os.getenv('CDK_DEFAULT_REGION')
            ),
            vpc=self.network.vpc,
            queue=self.queues.default_queue,
            domain_certificate=self.variables.domain_certificate,
            env_vars=self.app_env_vars,
            secrets=self.variables.app_secrets,
            task_cpu=256,
            task_memory_mib=512,
            task_desired_count=self.app_task_min_scaling_capacity,
            task_min_scaling_capacity=self.app_task_min_scaling_capacity,
            task_max_scaling_capacity=self.app_task_max_scaling_capacity,
        )
        # Grant permissions to the app to put messages in hte queue
        self.queues.default_queue.grant_send_messages(
            self.django_app.alb_fargate_service.service.task_definition.task_role
        )
        workers = BackendWorkersStack(
            self,
            "Workers",
            env=Environment(
                account=os.getenv('CDK_DEFAULT_ACCOUNT'),
                region=os.getenv('CDK_DEFAULT_REGION')
            ),
            vpc=self.network.vpc,
            ecs_cluster=self.django_app.ecs_cluster,
            queue=self.queues.default_queue,
            env_vars=self.app_env_vars,
            secrets=self.variables.app_secrets,
            task_cpu=256,
            task_memory_mib=512,
            task_min_scaling_capacity=self.worker_task_min_scaling_capacity,
            task_max_scaling_capacity=self.worker_task_max_scaling_capacity,
            scaling_steps=self.worker_scaling_steps
        )
        # Route requests made in the domain to the ALB
        dns = DnsRouteToAlbStack(
            self,
            "DnsToAlb",
            env=Environment(
                account=os.getenv('CDK_DEFAULT_ACCOUNT'),
                region=os.getenv('CDK_DEFAULT_REGION')
            ),
            domain_name=self.domain_name,
            subdomain=self.subdomain,
            alb=self.django_app.alb_fargate_service.load_balancer,
        )
