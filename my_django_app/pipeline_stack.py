import os
from constructs import Construct
from aws_cdk import (
    Stack,
    pipelines as pipelines,
)


class MyDjangoAppPipelineStack(Stack):
    def __init__(
            self,
            scope: Construct,
            id: str,
            repository: str,
            branch: str,
            gh_connection_arn: str,
            **kwargs
    ) -> None:
        super().__init__(scope, id, **kwargs)
        self.repository = repository
        self.branch = branch
        self.gh_connection_arn = gh_connection_arn
        self.pipeline = pipelines.CodePipeline(
            self,
            "Pipeline",
            synth=pipelines.ShellStep(
                "Synth",
                input=pipelines.CodePipelineSource.connection(
                    self.repository,
                    self.branch,
                    connection_arn=self.gh_connection_arn
                ),
                commands=[
                    "npm install -g aws-cdk",  # Installs the cdk cli on Codebuild
                    "pip install -r requirements.txt",  # Instructs Codebuild to install required packages
                    "npx cdk synth",
                ]
            ),
        )
