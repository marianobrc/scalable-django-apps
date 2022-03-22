import json
import boto3
from django.core.management import BaseCommand
from django.conf import settings

client = boto3.client(
    'ecs',
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    region_name=settings.AWS_REGION_NAME,
)


# This method runs the scraper as a task in AWS ECS Fargate, using boto.
def run_task_in_fargate(docker_cmd, config):

    # Call AWS API
    aws_response = client.run_task(
        cluster=config["cluster"],
        # Let it use the latest active revision of the task
        taskDefinition=config["taskDefinition"],
        count=1,
        enableECSManagedTags=False,
        group=config["group"],
        launchType='FARGATE',
        networkConfiguration={
            'awsvpcConfiguration': {
                'subnets': config["subnets"],
                'securityGroups': config["securityGroups"],
                'assignPublicIp': 'DISABLED'
            }
        },
        overrides={
            'containerOverrides': [
                {
                    'name': config["container"],
                    'command': docker_cmd,
                    'environment': config["environment"],
                },
            ],
            'executionRoleArn': config["executionRoleArn"],
            'taskRoleArn': config["taskRoleArn"]
        }
    )
    return aws_response


class Command(BaseCommand):
    help = "Runs a command inside a fargate task in ECS"

    def add_arguments(self, parser):
        parser.add_argument(
            dest="command",
            type=str,
            nargs="?"
        )
        parser.add_argument(
            "-c"
            "--config-file",
            dest="config_file_path",
            type=str
        )

    def handle(self, *args, **options):
        config_file_path = options["config_file_path"]
        docker_cmd = options["command"].split(" ")
        with open(config_file_path, "rb") as json_file:
            config = json.load(json_file)
            print(f"Config loaded from:{config_file_path}")
            print(f"Starting task in ECS with command:\n{' '.join(docker_cmd)}")
            aws_response = run_task_in_fargate(docker_cmd=docker_cmd, config=config)
            print(f"AWS Response:\n{aws_response}")
