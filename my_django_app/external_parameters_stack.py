from aws_cdk import (
    Stack,
    aws_ecs as ecs,
    aws_secretsmanager as secretsmanager,
    aws_ssm as ssm,
    aws_certificatemanager as acm
)
from constructs import Construct


class ExternalParametersStack(Stack):

    def __init__(
            self,
            scope: Construct,
            construct_id: str,
            database_secrets: secretsmanager.ISecret,
            name_prefix: str,  # Naming convention for parameters: i.e; /AppNameStageName/SecretName
            **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Secret values required by the app which are store in the Secrets Manager
        # This values will be injected as env vars on runtime
        self.app_secrets = {
            "DJANGO_SECRET_KEY": ecs.Secret.from_secrets_manager(
                secretsmanager.Secret.from_secret_name_v2(
                    self,
                    f"DjangoKeySecret",
                    secret_name=f"{name_prefix}DjangoSecretKey"
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
                field="dbname"
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
                    self,
                    f"AWSAccessKeyIDSecret",
                    secret_name=f"{name_prefix}AwsApiKeyId"
                )
            ),
            "AWS_SECRET_ACCESS_KEY": ecs.Secret.from_secrets_manager(
                secretsmanager.Secret.from_secret_name_v2(
                    self,
                    f"AWSAccessKeySecretSecret",
                    secret_name=f"{name_prefix}AwsApiKeySecret",
                )
            ),
        }
        # Retrieve the arn of the TLS certificate from SSM Parameter Store
        self.certificate_arn = ssm.StringParameter.value_for_string_parameter(
            self, f"{name_prefix}CertificateArn"
        )
        # Instantiate the certificate which will be required by the load balancer later
        self.domain_certificate = acm.Certificate.from_certificate_arn(
            self, "DomainCertificate",
            certificate_arn=self.certificate_arn
        )
