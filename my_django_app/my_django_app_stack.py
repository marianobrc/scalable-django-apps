from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    aws_sqs as sqs,
    aws_ecs as ecs,
    aws_ecs_patterns as ecs_patterns,
    aws_certificatemanager as acm,
    aws_elasticloadbalancingv2 as elbv2,
    aws_ssm as ssm
)
from constructs import Construct


class MyDjangoAppStack(Stack):

    def __init__(
            self,
            scope: Construct,
            construct_id: str,
            vpc: ec2.Vpc,
            ecs_cluster: ecs.Cluster,
            queue: sqs.Queue,
            domain_certificate: acm.ICertificate,
            env_vars: dict,
            secrets: dict,
            task_cpu: int = 256,
            task_memory_mib: int = 1024,
            task_desired_count: int = 2,
            task_min_scaling_capacity: int = 2,
            task_max_scaling_capacity: int = 4,
            **kwargs
    ) -> None:

        super().__init__(scope, construct_id, **kwargs)
        self.vpc = vpc
        self.ecs_cluster = ecs_cluster
        self.queue = queue
        self.domain_certificate = domain_certificate
        self.env_vars = env_vars
        self.secrets = secrets
        self.task_cpu = task_cpu
        self.task_memory_mib = task_memory_mib
        self.task_desired_count = task_desired_count
        self.task_min_scaling_capacity = task_min_scaling_capacity
        self.task_max_scaling_capacity = task_max_scaling_capacity

        # Prepare environment variables
        self.container_name = f"django_app"

        # Create the load balancer, ECS service and fargate task for teh Django App
        self.alb_fargate_service = ecs_patterns.ApplicationLoadBalancedFargateService(
            self,
            f"MyDjangoApp",
            protocol=elbv2.ApplicationProtocol.HTTPS,
            certificate=self.domain_certificate,
            redirect_http=True,
            platform_version=ecs.FargatePlatformVersion.VERSION1_4,
            cluster=self.ecs_cluster,  # Required
            #task_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_ISOLATED),
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
                secrets=self.secrets
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
        # Save useful values in in SSM
        self.ecs_cluster_name_param = ssm.StringParameter(
            self,
            "EcsClusterNameParam",
            parameter_name=f"/{scope.stage_name}/EcsClusterNameParam",
            string_value=self.ecs_cluster.cluster_name
        )
        self.task_def_arn_param = ssm.StringParameter(
            self,
            "TaskDefArnParam",
            parameter_name=f"/{scope.stage_name}/TaskDefArnParam",
            string_value=self.alb_fargate_service.task_definition.task_definition_arn
        )
        self.task_def_family_param = ssm.StringParameter(
            self,
            "TaskDefFamilyParam",
            parameter_name=f"/{scope.stage_name}/TaskDefFamilyParam",
            string_value=f"family:{self.alb_fargate_service.task_definition.family}"
        )
        self.exec_role_arn_param = ssm.StringParameter(
            self,
            "TaskExecRoleArnParam",
            parameter_name=f"/{scope.stage_name}/TaskExecRoleArnParam",
            string_value=self.alb_fargate_service.task_definition.execution_role.role_arn
        )
        self.task_role_arn_param = ssm.StringParameter(
            self,
            "TaskRoleArnParam",
            parameter_name=f"/{scope.stage_name}/TaskRoleArnParam",
            string_value=self.alb_fargate_service.task_definition.task_role.role_arn
        )
