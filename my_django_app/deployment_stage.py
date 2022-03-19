import os
from constructs import Construct
from aws_cdk import (
    Stage,
    Environment,
)
from my_django_app.network_stack import NetworkStack
from my_django_app.database_stack import DatabaseStack
from my_django_app.my_django_app_stack import MyDjangoAppStack
from my_django_app.static_files_stack import StaticFilesStack
from my_django_app.queues_stack import QueuesStack
from my_django_app.backend_workers_stack import BackendWorkersStack
from my_django_app.variables_stack import VariablesStack


class MyDjangoAppPipelineStage(Stage):

    def __init__(
            self,
            scope: Construct,
            id: str,
            django_settings_module: str,
            django_debug: bool,
            **kwargs
    ):

        super().__init__(scope, id, **kwargs)
        self.django_settings_module = django_settings_module
        self.django_debug = django_debug
        network = NetworkStack(
            self,
            "Network",
            env=Environment(
                account=os.getenv('CDK_DEFAULT_ACCOUNT'),
                region=os.getenv('CDK_DEFAULT_REGION')
            ),
        )
        database = DatabaseStack(
            self,
            "Database",
            env=Environment(
                account=os.getenv('CDK_DEFAULT_ACCOUNT'),
                region=os.getenv('CDK_DEFAULT_REGION')
            ),
            vpc=network.vpc,
            database_name="app_db",
            auto_pause_minutes=5
        )
        # Serve static files for the Backoffice (django-admin)
        static_files = StaticFilesStack(
            self,
            "StaticFiles",
            env=Environment(
                account=os.getenv('CDK_DEFAULT_ACCOUNT'),
                region=os.getenv('CDK_DEFAULT_REGION')
            ),
        )
        queues = QueuesStack(
            self,
            "Queues",
            env=Environment(
                account=os.getenv('CDK_DEFAULT_ACCOUNT'),
                region=os.getenv('CDK_DEFAULT_REGION')
            ),
        )
        app_env_vars = {
            "DJANGO_SETTINGS_MODULE": self.django_settings_module,
            "DJANGO_DEBUG": str(self.django_debug),
            # Workaround to use VPC endpoints with SQS in Django
            # https://github.com/boto/boto3/issues/1900#issuecomment-873597264
            "AWS_DATA_PATH": "/home/web/botocore/",
            "AWS_ACCOUNT_ID": os.getenv('CDK_DEFAULT_ACCOUNT'),
            "AWS_STATIC_FILES_BUCKET_NAME":  static_files.s3_bucket.bucket_name,
            "AWS_STATIC_FILES_CLOUDFRONT_URL": static_files.cloudfront_distro.distribution_domain_name,
            "CELERY_BROKER_URL": queues.default_queue.queue_url,
            "CELERY_TASK_ALWAYS_EAGER": "False"
        }
        variables = VariablesStack(
            self,
            "AppVariables",
            env=Environment(
                account=os.getenv('CDK_DEFAULT_ACCOUNT'),
                region=os.getenv('CDK_DEFAULT_REGION')
            ),
            database_secrets=database.aurora_serverless_db.secret,
        )
        django_app = MyDjangoAppStack(
            self,
            "AppService",
            env=Environment(
                account=os.getenv('CDK_DEFAULT_ACCOUNT'),
                region=os.getenv('CDK_DEFAULT_REGION')
            ),
            vpc=network.vpc,
            queue=queues.default_queue,
            domain_certificate=variables.domain_certificate,
            env_vars=app_env_vars,
            secrets=variables.app_secrets,
            task_cpu=256,
            task_memory_mib=512,
            task_desired_count=2,
            task_min_scaling_capacity=2,  # 2 minimum to get High Availability
            task_max_scaling_capacity=5,  # Limit the scaling to save costs
        )
        # Grant permissions to the app to put messages in hte queue
        queues.default_queue.grant_send_messages(django_app.alb_fargate_service.service.task_definition.task_role)
        workers = BackendWorkersStack(
            self,
            "Workers",
            env=Environment(
                account=os.getenv('CDK_DEFAULT_ACCOUNT'),
                region=os.getenv('CDK_DEFAULT_REGION')
            ),
            vpc=network.vpc,
            ecs_cluster=django_app.ecs_cluster,
            queue=queues.default_queue,
            env_vars=app_env_vars,
            secrets=variables.app_secrets,
            task_cpu=256,
            task_memory_mib=512,
            task_min_scaling_capacity=1,
            task_max_scaling_capacity=2,  # Limit the scaling to save costs
            scaling_steps=[
                {"upper": 0, "change": 0},  # 0 msgs = 1 workers
                {"lower": 10, "change": +1},  # 10 msgs = 2 workers
            ]
        )
