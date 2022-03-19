import json
import os
import argparse
import subprocess


def init_argparse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Set parameters in AWS SSM Parameter Store or Secrets Manager"
    )
    parser.add_argument(
        "file",
        help="A json file with parameters.",
    )
    parser.add_argument(
        "--profile",
        dest="profile",
        help="Set the profile to use with the aws client.",
        required=False
    )
    parser.add_argument(
        "--tags",
        dest="tags",
        help="Add tags in Key=Value format, e.g. Key=project,Value=MyDjangoApp",
        required=False
    )
    parser.add_argument(
        "--overwrite",
        help="The parameter will be overwriten",
        dest="is_overwrite",
        action="store_true",
        default=False
    )
    parser.add_argument(
        "--secret",
        help="The parameters will be saved as secrets in the Secrets Manager",
        dest="is_secret",
        action="store_true",
        default=False
    )
    return parser


if __name__ == "__main__":
    parser = init_argparse()
    args = parser.parse_args()
    print("Settings parameters in AWS..")
    with open(args.file, "r") as parameters_file:
        parameters = json.load(parameters_file)
        for key, value in parameters.items():
            command = ["aws"]
            if args.profile:
                command.extend(["--profile", args.profile])
            if args.is_secret:  # Secret in secrets manager
                command.extend(["secretsmanager", "create-secret", "--name", key, "--secret-string", value])
                if args.is_overwrite:
                    command.extend(["--force-overwrite-replica-secret"])
            else:  # Regular parameter in SSM
                command.extend(["ssm", "put-parameter", "--name", key, "--value", value, "--type", "String"])
                if args.is_overwrite:
                    command.extend(["--overwrite"])
                elif args.tags:
                    command.extend(["--tags", args.tags])
            print(command)
            response = subprocess.call(command)
    print("Finished.")
