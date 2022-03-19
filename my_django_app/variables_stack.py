from aws_cdk import (
    Stack,
    aws_ecs as ecs,
    aws_secretsmanager as secretsmanager,
    aws_ssm as ssm,
    aws_certificatemanager as acm
)
from constructs import Construct


class VariablesStack(Stack):

    def __init__(
            self,
            scope: Construct,
            construct_id: str,
            database_secrets: secretsmanager.ISecret,
            **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.app_secrets = {
            "DJANGO_SECRET_KEY": ecs.Secret.from_secrets_manager(
                secretsmanager.Secret.from_secret_name_v2(
                    self,
                    f"AWSDjangoKeySecret",
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
                    self,
                    f"AWSAccessKeyIDSecret",
                    secret_name="/mydjangoapp/awsapikeyid"
                )
            ),
            "AWS_SECRET_ACCESS_KEY": ecs.Secret.from_secrets_manager(
                secretsmanager.Secret.from_secret_name_v2(
                    self,
                    f"AWSAccessKeySecretSecret",
                    secret_name="/mydjangoapp/awsapikeysecret",
                )
            ),
        }
        self.certificate_arn = ssm.StringParameter.value_for_string_parameter(
            self, "/mydjangoapp/certificatearn"
        )
        self.domain_certificate = acm.Certificate.from_certificate_arn(
            self, f"DomainCertificate",
            certificate_arn=self.certificate_arn
        )
