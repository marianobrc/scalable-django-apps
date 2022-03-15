from aws_cdk import (
    # Duration,
    Stack,
    aws_ec2 as ec2,
)
from constructs import Construct


class NetworkingStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        app_name = kwargs.pop("app_name", "quickpay").lower().strip()
        deploy_env = kwargs.pop("deploy_env", "PROD").upper()
        super().__init__(scope, construct_id, **kwargs)

        # Our network in the cloud
        self.vpc = ec2.Vpc(
            self,
            f"{app_name}Vpc{deploy_env}",
            max_azs=2,  # default is all AZs in region
            nat_gateways=1,  # One Nat GW is required for third-party integrations like Sentry
            enable_dns_hostnames=True,
            enable_dns_support=True
        )
        # Add VPC endpoints for ECR, S3 and CloudWatch to avoid using NAT GWs
        self.s3_private_link = ec2.GatewayVpcEndpoint(
            self,
            f"{app_name}S3GWEndpoint{deploy_env}",
            vpc=self.vpc,
            service=ec2.GatewayVpcEndpointAwsService.S3
        )
        self.ecr_api_private_link = ec2.InterfaceVpcEndpoint(
            self,
            f"{app_name}ECRapiEndpoint{deploy_env}",
            vpc=self.vpc,
            service=ec2.InterfaceVpcEndpointAwsService.ECR,
            open=True,
            private_dns_enabled=True
        )
        self.ecr_dkr_private_link = ec2.InterfaceVpcEndpoint(
            self,
            f"{app_name}ECRdkrEndpoint{deploy_env}",
            vpc=self.vpc,
            service=ec2.InterfaceVpcEndpointAwsService.ECR_DOCKER,
            open=True,
            private_dns_enabled=True
        )
        self.cloudwatch_private_link = ec2.InterfaceVpcEndpoint(
            self,
            f"{app_name}CloudWatchEndpoint{deploy_env}",
            vpc=self.vpc,
            service=ec2.InterfaceVpcEndpointAwsService.CLOUDWATCH_LOGS,
            open=True,
            private_dns_enabled=True
        )
        self.secrets_manager_private_link = ec2.InterfaceVpcEndpoint(
            self,
            f"{app_name}SecretsManagerEndpoint{deploy_env}",
            vpc=self.vpc,
            service=ec2.InterfaceVpcEndpointAwsService.SECRETS_MANAGER,
            open=True,
            private_dns_enabled=True
        )
        self.sqs_private_link = ec2.InterfaceVpcEndpoint(
            self,
            f"{app_name}SQSEndpoint{deploy_env}",
            vpc=self.vpc,
            service=ec2.InterfaceVpcEndpointAwsService.SQS,
            open=True,
            private_dns_enabled=True
        )
