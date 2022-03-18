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
        django_app = MyDjangoAppStack(
            self,
            "MyDjangoAppService",
            env=Environment(
                account=os.getenv('CDK_DEFAULT_ACCOUNT'),
                region=os.getenv('CDK_DEFAULT_REGION')
            ),
            vpc=network.vpc,
            queue=queues.default_queue,
            static_files_bucket=static_files.s3_bucket,
            static_files_cloudfront_dist=static_files.cloudfront_distro,
            certificate_arn=os.getenv('CDK_DOMAIN_CERTIFICATE_ARN'),
            django_settings_module="app.settings.prod",
            sm_django_secret_name="/mydjangoapp/djangosecretkey/prod",
            sm_db_secret_name="/mydjangoapp/dbsecrets/prod",
            sm_aws_api_key_id_secret_name="/mydjangoapp/awsapikeyid",
            sm_aws_api_key_secret_secret_name="/mydjangoapp/awsapikeysecret",
            django_debug=False,
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
            django_settings_module="app.settings.prod",
            sm_django_secret_name="/mydjangoapp/djangosecretkey/prod",
            sm_db_secret_name="/mydjangoapp/dbsecrets/prod",
            sm_aws_api_key_id_secret_name="/mydjangoapp/awsapikeyid",
            sm_aws_api_key_secret_secret_name="/mydjangoapp/awsapikeysecret",
            django_debug=False,
            task_cpu=256,
            task_memory_mib=512,
            task_min_scaling_capacity=1,
            task_max_scaling_capacity=2,  # Limit the scaling to save costs
            scaling_steps=[
                {"upper": 0, "change": 0},  # 0 msgs = 1 workers
                {"lower": 10, "change": +1},  # 10 msgs = 2 workers
            ]
        )
