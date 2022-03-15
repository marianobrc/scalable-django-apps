from aws_cdk import (
    # Duration,
    Stack,
    aws_ec2 as ec2,
)
from constructs import Construct


class NetworkStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Our network in the cloud
        self.vpc = ec2.Vpc(
            self,
            "VPC",
            max_azs=2,  # default is all AZs in region
            nat_gateways=0,  # No Nat GWs are required as we will add VPC endpoints
            enable_dns_hostnames=True,
            enable_dns_support=True
        )
        # Add VPC endpoints to keep the traffic inside AWS
        self.s3_private_link = ec2.GatewayVpcEndpoint(
            self,
            "S3GWEndpoint",
            vpc=self.vpc,
            service=ec2.GatewayVpcEndpointAwsService.S3
        )
        self.ecr_api_private_link = ec2.InterfaceVpcEndpoint(
            self,
            "ECRapiEndpoint",
            vpc=self.vpc,
            service=ec2.InterfaceVpcEndpointAwsService.ECR,
            open=True,
            private_dns_enabled=True
        )
        self.ecr_dkr_private_link = ec2.InterfaceVpcEndpoint(
            self,
            "ECRdkrEndpoint",
            vpc=self.vpc,
            service=ec2.InterfaceVpcEndpointAwsService.ECR_DOCKER,
            open=True,
            private_dns_enabled=True
        )
        self.cloudwatch_private_link = ec2.InterfaceVpcEndpoint(
            self,
            "CloudWatchEndpoint",
            vpc=self.vpc,
            service=ec2.InterfaceVpcEndpointAwsService.CLOUDWATCH_LOGS,
            open=True,
            private_dns_enabled=True
        )
        self.secrets_manager_private_link = ec2.InterfaceVpcEndpoint(
            self,
            "SecretsManagerEndpoint",
            vpc=self.vpc,
            service=ec2.InterfaceVpcEndpointAwsService.SECRETS_MANAGER,
            open=True,
            private_dns_enabled=True
        )
        self.sqs_private_link = ec2.InterfaceVpcEndpoint(
            self,
            "SQSEndpoint",
            vpc=self.vpc,
            service=ec2.InterfaceVpcEndpointAwsService.SQS,
            open=True,
            private_dns_enabled=True
        )
