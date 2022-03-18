import os
from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    aws_sqs as sqs,
    aws_s3 as s3,
    aws_cloudfront as cloudfront,
    aws_ecs as ecs,
    aws_ecs_patterns as ecs_patterns,
    aws_secretsmanager as secretsmanager,
    aws_certificatemanager as acm,
    aws_elasticloadbalancingv2 as elbv2
)
from constructs import Construct


class MyDjangoAppStack(Stack):

    def __init__(
            self,
            scope: Construct,
            construct_id: str,
            vpc: ec2.Vpc,
            queue: sqs.Queue,
            static_files_bucket: s3.Bucket,
            static_files_cloudfront_dist: cloudfront.CloudFrontWebDistribution,
            certificate_arn: str,
            django_settings_module: str,
            sm_django_secret_name: str,
            sm_db_secret_name: str,  # Name of a secret in Secrets Manager containing database credentials
            sm_aws_api_key_id_secret_name: str,
            sm_aws_api_key_secret_secret_name: str,
            django_debug: bool = False,
            task_cpu: int = 256,
            task_memory_mib: int = 1024,
            task_desired_count: int = 2,
            task_min_scaling_capacity: int = 2,
            task_max_scaling_capacity: int = 4,
            **kwargs
    ) -> None:

        super().__init__(scope, construct_id, **kwargs)
        self.vpc = vpc
        self.static_files_bucket = static_files_bucket
        self.static_files_cloudfront_dist = static_files_cloudfront_dist
        self.certificate_arn = certificate_arn
        self.django_settings_module = django_settings_module.lower().strip()
        self.sm_django_secret_name = sm_django_secret_name
        self.sm_db_secret_name = sm_db_secret_name
        self.sm_aws_api_key_id_secret_name = sm_aws_api_key_id_secret_name
        self.sm_aws_api_key_secret_secret_name = sm_aws_api_key_secret_secret_name
        self.django_debug = django_debug
        self.task_cpu = task_cpu
        self.task_memory_mib = task_memory_mib
        self.task_desired_count = task_desired_count
        self.task_min_scaling_capacity = task_min_scaling_capacity
        self.task_max_scaling_capacity = task_max_scaling_capacity

        self.ecs_cluster = ecs.Cluster(self, f"ECSCluster", vpc=vpc)

        # Prepare environment variables
        self.container_name = f"django_app"
        self.env_vars = {
            "DJANGO_SETTINGS_MODULE": self.django_settings_module,
            "DJANGO_DEBUG": str(self.django_debug),
            "AWS_SM_DJANGO_SECRET_NAME": sm_django_secret_name,
            "AWS_SM_DB_SECRET_NAME": self.sm_db_secret_name,
            # Workaround to use VPC endpoints with SQS in Django
            # https://github.com/boto/boto3/issues/1900#issuecomment-873597264
            "AWS_DATA_PATH": "/home/web/botocore/",
            "AWS_ACCOUNT_ID": os.getenv('CDK_DEFAULT_ACCOUNT'),
            "AWS_STATIC_FILES_BUCKET_NAME": self.static_files_bucket.bucket_name,
            "AWS_STATIC_FILES_CLOUDFRONT_URL": self.static_files_cloudfront_dist.distribution_domain_name,
            "CELERY_BROKER_URL": queue.queue_url,
            "CELERY_TASK_ALWAYS_EAGER": "False"
        }
        # Create the load balancer, ECS service and fargate task for teh Django App
        self.alb_fargate_service = ecs_patterns.ApplicationLoadBalancedFargateService(
            self,
            f"MyDjangoApp",
            protocol=elbv2.ApplicationProtocol.HTTPS,
            certificate=acm.Certificate.from_certificate_arn(
                self, f"MyDjangoAppDomainCertificate",
                certificate_arn=certificate_arn
            ),
            platform_version=ecs.FargatePlatformVersion.VERSION1_4,
            cluster=self.ecs_cluster,  # Required
            cpu=self.task_cpu,  # Default is 256
            memory_limit_mib=self.task_memory_mib,  # Default is 512
            desired_count=self.task_desired_count,  # Default is 1
            task_image_options=ecs_patterns.ApplicationLoadBalancedTaskImageOptions(
                image=ecs.ContainerImage.from_asset(
                    directory="app/",
                    file="docker/app/Dockerfile",
                    target="prod"
                ),
                container_name=self.container_name,
                container_port=8000,
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
            ),
            public_load_balancer=True
        )
        # Set the health checks settings
        self.alb_fargate_service.target_group.configure_health_check(
            path="/status/",
            healthy_threshold_count=3,
            unhealthy_threshold_count=2
        )
        # Autoscaling based on CPU utilization
        scalable_target = self.alb_fargate_service.service.auto_scale_task_count(
            min_capacity=self.task_min_scaling_capacity,
            max_capacity=self.task_max_scaling_capacity
        )
        scalable_target.scale_on_cpu_utilization(
            f"CpuScaling",
            target_utilization_percent=75,
        )

