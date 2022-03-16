import typing
from aws_cdk import (
    Duration,
    Stack,
    aws_rds as rds,
    aws_ec2 as ec2
)
from constructs import Construct


class DatabaseStack(Stack):

    def __init__(
            self,
            scope: Construct,
            construct_id: str,
            vpc: typing.Optional[ec2.Vpc],
            auto_pause_minutes: int = 30,
            backup_retention_days: int = 1,
            **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        self.vpc = vpc
        self.auto_pause_minutes = auto_pause_minutes
        self.backup_retention_days = backup_retention_days

        # Our network in the cloud
        self.aurora_serverless_db = rds.ServerlessCluster(
            self,
            "AuroraServerlessCluster",
            engine=rds.DatabaseClusterEngine.AURORA_POSTGRESQL,
            vpc=self.vpc,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_ISOLATED),
            backup_retention=Duration.days(self.backup_retention_days),  # 1 day retention is free
            cluster_identifier=f"dbcluster{construct_id.lower()}",
            deletion_protection=True,
            enable_data_api=True,  # Allow running queries in AWS console (free)
            parameter_group=rds.ParameterGroup.from_parameter_group_name(  # Specify the postgresql version
                self,
                "AuroraDBParameterGroup",
                "default.aurora-postgresql10"  # Only this version is supported for Aurora Serverless now
            ),
            scaling=rds.ServerlessScalingOptions(
                auto_pause=Duration.minutes(self.auto_pause_minutes),  # Shutdown after minutes of inactivity to save costs
                min_capacity=rds.AuroraCapacityUnit.ACU_2,  # The minimal capacity for postgresql allowed here is 2
                max_capacity=rds.AuroraCapacityUnit.ACU_4   # Limit scaling to limit costs
            ),
        )
        # Allow ingress traffic from ECS tasks
        self.aurora_serverless_db.connections.allow_default_port_from_any_ipv4(
            description="Services in private subnets can access the DB"
        )
