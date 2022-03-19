import os
from constructs import Construct
from aws_cdk import (
    Stage,
    Environment,
    aws_ecs as ecs,
    aws_secretsmanager as secretsmanager,
    aws_certificatemanager as acm
)
from my_django_app.network_stack import NetworkStack
from my_django_app.database_stack import DatabaseStack
from my_django_app.my_django_app_stack import MyDjangoAppStack
from my_django_app.static_files_stack import StaticFilesStack
from my_django_app.queues_stack import QueuesStack
from my_django_app.backend_workers_stack import BackendWorkersStack


class MyDjangoAppPipelineStage(Stage):

    def __init__(
            self,
            scope: Construct,
            id: str,
            **kwargs
    ):

        super().__init__(scope, id, **kwargs)

        network = NetworkStack(
            self,
            "MyDjangoAppNetwork",
            env=Environment(
                account=os.getenv('CDK_DEFAULT_ACCOUNT'),
                region=os.getenv('CDK_DEFAULT_REGION')
            ),
        )
        database = DatabaseStack(
            self,
            "MyDjangoAppDatabase",
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
            "MyDjangoAppStaticFiles",
            env=Environment(
                account=os.getenv('CDK_DEFAULT_ACCOUNT'),
                region=os.getenv('CDK_DEFAULT_REGION')
            ),
        )
        queues = QueuesStack(
            self,
            "MyDjangoAppQueues",
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
            "AWS_STATIC_FILES_BUCKET_NAME": self.static_files_bucket.bucket_name,
            "AWS_STATIC_FILES_CLOUDFRONT_URL": self.static_files_cloudfront_dist.distribution_domain_name,
            "CELERY_BROKER_URL": queues.default_queue.queue_url,
            "CELERY_TASK_ALWAYS_EAGER": "False"
        }
        database_secrets = database.aurora_serverless_db.secret.secret_name
        app_secrets = {
            "DJANGO_SECRET_KEY": ecs.Secret.from_secrets_manager(
                secretsmanager.Secret.from_secret_name_v2(
                    self, f"AWSDjangoKeySecret",
                    secret_name="/mydjangoapp/djangosecretkey/prod"
                )
            ),
            "DB_HOST": ecs.Secret.from_secrets_manager(
                database_secrets,
                field="host"
            ),
            "DB_PORT": ecs.Secret.from_secrets_manager(
                database_secrets,
                field="port"
            ),
            "DB_NAME": ecs.Secret.from_secrets_manager(
                database_secrets,
                field="dbInstanceIdentifier"
            ),
            "DB_USER": ecs.Secret.from_secrets_manager(
                database_secrets,
                field="username"
            ),
            "DB_PASSWORD": ecs.Secret.from_secrets_manager(
                database_secrets,
                field="password"
            ),
            "AWS_ACCESS_KEY_ID": ecs.Secret.from_secrets_manager(
                secretsmanager.Secret.from_secret_name_v2(
                    self, f"AWSAccessKeyIDSecret",
                    secret_name="/mydjangoapp/awsapikeyid"
                )
            ),
            "AWS_SECRET_ACCESS_KEY": ecs.Secret.from_secrets_manager(
                secretsmanager.Secret.from_secret_name_v2(
                    self, f"AWSAccessKeySecretSecret",
                    secret_name="/mydjangoapp/awsapikeysecret",
                )
            ),
        }
        certificate_arn = os.getenv('CDK_DOMAIN_CERTIFICATE_ARN')
        domain_certificate = acm.Certificate.from_certificate_arn(
            self, f"MyDjangoAppDomainCertificate",
            certificate_arn=certificate_arn
        )
        django_app = MyDjangoAppStack(
            self,
            "MyDjangoAppService",
            env=Environment(
                account=os.getenv('CDK_DEFAULT_ACCOUNT'),
                region=os.getenv('CDK_DEFAULT_REGION')
            ),
            vpc=network.vpc,
            queue=queues.default_queue,
            domain_certificate=domain_certificate,
            env_vars=app_env_vars,
            secrets=app_secrets,
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
            "MyDjangoAppWorkers",
            env=Environment(
                account=os.getenv('CDK_DEFAULT_ACCOUNT'),
                region=os.getenv('CDK_DEFAULT_REGION')
            ),
            vpc=network.vpc,
            ecs_cluster=django_app.ecs_cluster,
            queue=queues.default_queue,
            env_vars=app_env_vars,
            secrets=app_secrets,
            task_cpu=256,
            task_memory_mib=512,
            task_min_scaling_capacity=1,
            task_max_scaling_capacity=2,  # Limit the scaling to save costs
            scaling_steps=[
                {"upper": 0, "change": 0},  # 0 msgs = 1 workers
                {"lower": 10, "change": +1},  # 10 msgs = 2 workers
            ]
        )
