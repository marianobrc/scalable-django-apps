import os
import json
import boto3
from django.core.management import BaseCommand
from django.conf import settings

ecs_client = boto3.client(
    'ecs',
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    region_name=settings.AWS_REGION_NAME,
)

ssm_client = boto3.client(
    'ssm',
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    region_name=settings.AWS_REGION_NAME,
)

secrets_client = boto3.client(
    'secretsmanager',
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    region_name=settings.AWS_REGION_NAME,
)


aws_ssm_parameters_map = {
        "vpcId": "VpcId",
        "cluster": "EcsClusterNameParam",
        "taskDefinition": "TaskDefArnParam",
        "group": "TaskDefFamilyParam",
        "subnets": [],
        "securityGroups": [],
        "executionRoleArn": "TaskExecRoleArnParam",
        "taskRoleArn": "TaskRoleArnParam"
}
aws_ssm_parameters = [
        "VpcId",
        "EcsClusterNameParam",
        "TaskDefArnParam",
        "TaskDefFamilyParam",
        "TaskExecRoleArnParam",
        "TaskRoleArnParam"
]


def _build_execution_cofig(env_name, extra_env_vars=None):
    # Get the parameters stored in SSM
    config = {}

    for p in aws_ssm_parameters:
        response = ssm_client.get_parameter(
            Name=f"/{env_name}/{p}"
        )
        config[p] = response['Parameter']['Value']

    # Networking config
    response = ssm_client.get_parameter(
        Name=f"/{env_name}/VpcPrivateSubnetsParam"
    )
    config["subnets"] = response['Parameter']['Value'].split(',')
    # Let it use the default security group
    # config["securityGroups"] = [
    #     "sg-011d894ce2289d62b"
    # ]
    config["container"] = "django_app"
    # Env vars for running django commands
    config["environment"] = [
        # Regular parameters
        {
            "name": "DJANGO_SETTINGS_MODULE",
            "value": "app.settings.stage"
        },
        {
            "name": "DJANGO_DEBUG",
            "value": "True"
        },
        {
            "name": "AWS_ACCOUNT_ID",
            "value": settings.AWS_ACCOUNT_ID
        },
        {
            "name": "CELERY_TASK_ALWAYS_EAGER",
            "value": "False"
        }
    ]
    # Retrieve extra env var values from SSM Parameter Store
    response = ssm_client.get_parameter(
        Name=f"/{env_name}/StaticFilesBucketNameParam"
    )
    config["environment"].append(
        {
            "name": "AWS_STATIC_FILES_BUCKET_NAME",
            "value": response['Parameter']['Value']
        }
    )
    response = ssm_client.get_parameter(
        Name=f"/{env_name}/StaticFilesCloudFrontUrlParam"
    )
    config["environment"].append(
        {
            "name": "AWS_STATIC_FILES_CLOUDFRONT_URL",
            "value": response['Parameter']['Value']
        }
    )
    response = ssm_client.get_parameter(
        Name=f"/{env_name}/SqsDefaultQueueUrlParam"
    )
    config["environment"].append(
        {
            "name": "SQS_DEFAULT_QUEUE_URL",
            "value": response['Parameter']['Value']
        }
    )

    # Retrieve secret values from secrets manager
    response = secrets_client.get_secret_value(
        SecretId=f"/{env_name}/DjangoSecretKey"
    )
    config["environment"].append(
        {
            "name": "DJANGO_SECRET_KEY",
            "value": response['SecretString']
        }
    )
    # Get the name of the secret containing database secrets from SSM
    response = ssm_client.get_parameter(
        Name=f"/{env_name}/DatabaseSecretNameParam"
    )
    db_secret_name = response['Parameter']['Value']
    # Now get the actual secrets from secrets manager
    response = secrets_client.get_secret_value(
        SecretId=db_secret_name
    )
    db_secrets = json.loads(
        response['SecretString']
    )
    config["environment"].append(
        {
            "name": "DB_HOST",
            "value": db_secrets['host']
        }
    )
    config["environment"].append(
        {
            "name": "DB_PORT",
            "value": str(db_secrets['port'])
        }
    )
    config["environment"].append(
        {
            "name": "DB_USER",
            "value": db_secrets['username']
        }
    )
    config["environment"].append(
        {
            "name": "DB_PASSWORD",
            "value": db_secrets['password']
        }
    )
    config["environment"].append(
        {
            "name": "AWS_ACCESS_KEY_ID",
            "value": settings.AWS_ACCESS_KEY_ID
        }
    )
    config["environment"].append(
        {
            "name": "AWS_SECRET_ACCESS_KEY",
            "value": settings.AWS_SECRET_ACCESS_KEY
        }
    )
    # Add extra env vars if any
    if extra_env_vars:
        for var in extra_env_vars:
            name, value = var.split('=', maxsplit=1)
            config["environment"].append(
                {
                    "name": name,
                    "value": value
                }
            )
    return config


# This method runs a command as a task in AWS ECS Fargate
def run_task_in_fargate(docker_cmd, config):

    # Call AWS API
    aws_response = ecs_client.run_task(
        cluster=config["EcsClusterNameParam"],
        # Let it use the latest active revision of the task
        taskDefinition=config["TaskDefArnParam"],
        count=1,
        enableECSManagedTags=False,
        group=config["TaskDefFamilyParam"],
        launchType='FARGATE',
        networkConfiguration={
            'awsvpcConfiguration': {
                'subnets': config["subnets"],
                #'securityGroups': config["securityGroups"],
                'assignPublicIp': 'DISABLED'
            }
        },
        overrides={
            'containerOverrides': [
                {
                    'name': config["container"],
                    'command': docker_cmd.split(" "),  # Expects a list
                    'environment': config["environment"],
                },
            ],
            'executionRoleArn': config["TaskExecRoleArnParam"],
            'taskRoleArn': config["TaskRoleArnParam"]
        }
    )
    return aws_response


class Command(BaseCommand):
    help = "Runs a command inside a fargate task in ECS"

    def add_arguments(self, parser):
        parser.add_argument(
            "command",
            type=str,
            nargs=1
        )
        parser.add_argument(
            "--env",
            dest="env_name",
            help="The environment where the command will be run: MyDjangoAppStaging or MyDjangoAppProduction.",
            required=True
        )
        parser.add_argument(
            "--env-var",
            dest="env_vars",
            help="Set extra env vars as --env-var NAME1=VALUE1 --env-var NAME2=VALUE2",
            action='append',  # Make a list witht he multiple env vars
            required=False
        )

    def handle(self, *args, **options):
        env_name = options["env_name"]
        docker_cmd = options["command"][0]
        env_vars = options.get("env_vars")
        print(f"Building execution config for {env_name}")
        config = _build_execution_cofig(env_name=env_name, extra_env_vars=env_vars)
        print(f"Config loaded:\n{config}")
        print(f"Starting task in ECS with command:\n{docker_cmd}")
        aws_response = run_task_in_fargate(docker_cmd=docker_cmd, config=config)
        print(f"AWS Response:\n{aws_response}")
