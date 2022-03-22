import datetime
from aws_cdk import (
    Stack,
    CfnParameter,
    Fn,
    aws_events as events,
    aws_events_targets as targets,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_ecr as ecr,
    aws_ssm as ssm
)
from constructs import Construct


class RunTaskStack(Stack):

    def __init__(
            self,
            scope: Construct,
            construct_id: str,
            stage_name: str,  # MyDjangoAppStaging | MyDjangoAppProduction
            **kwargs
    ) -> None:

        super().__init__(scope, construct_id, **kwargs)
        self.command_parameter = CfnParameter(
            self, "command",
            type="String",
            description="A shell command to be executed in a Fargate task"
        )
        # Import parameters exported previously
        vpc_id = ssm.StringParameter.value_from_lookup(
            self,
            parameter_name=f"/{stage_name}/VpcId"
        )
        ecr_image_name = ssm.StringParameter.value_from_lookup(
            self,
            parameter_name=f"/{stage_name}/EcrImageName"
        )
        ecs_cluster_name = ssm.StringParameter.value_from_lookup(
            self,
            parameter_name=f"/{stage_name}/EcsClusterName"
        )
        self.ecs_cluster = ecs.Cluster.from_cluster_attributes(
            self, "ECSCluster",
            vpc=ec2.Vpc.from_lookup(
                self, "RunTaskVpc",
                vpc_id=vpc_id
            ),
            cluster_name=ecs_cluster_name,
            security_groups=[]
        )
        # Import the task definition created
        self.task_definition = ecs.FargateTaskDefinition(
            self, "TaskDef",
            cpu=256,
            memory_limit_mib=512
        )
        self.task_definition.add_container(
            f"{stage_name}RunTaskContainer",
            image=ecs.ContainerImage.from_ecr_repository(
                repository=ecr.Repository.from_repository_name(
                    self,
                    f"{stage_name}RunTaskImage",
                    repository_name=ecr_image_name
                )
            ),
            command=self.command_parameter.value_as_string.split(),
            container_name="standalone_command",
            cpu=256,
            memory_limit_mib=512
        )

        # Trigger the task in 5 minutes from now
        now = datetime.datetime.now()
        rule = events.Rule(
            self, "Rule",
            schedule=events.Schedule.cron(
                day=str(now.day),
                hour=str(now.hour),
                minute=str(now.minute + 5),
                month=str(now.month),
                year=str(now.year),
            )
        )
        # Run a standalone task in ECS, with the given command
        rule.add_target(targets.EcsTask(
            cluster=self.ecs_cluster,
            subnet_selection=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_ISOLATED),
            task_definition=self.task_definition,
            task_count=1,
        ))

