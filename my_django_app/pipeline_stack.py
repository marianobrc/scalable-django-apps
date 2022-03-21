import os
from constructs import Construct
from aws_cdk import (
    Stack,
    pipelines as pipelines,
    aws_ssm as ssm,
    aws_rds as rds,
)
from .deployment_stage import MyDjangoAppPipelineStage


class MyDjangoAppPipelineStack(Stack):
    def __init__(
            self,
            scope: Construct,
            id: str,
            repository: str,
            branch: str,
            ssm_gh_connection_param: str,
            **kwargs
    ) -> None:
        super().__init__(scope, id, **kwargs)
        self.repository = repository
        self.branch = branch
        self.ssm_gh_connection_param = ssm_gh_connection_param
        self.gh_connection_arn = ssm.StringParameter.value_for_string_parameter(
            self, ssm_gh_connection_param
        )
        pipeline = pipelines.CodePipeline(
            self,
            "Pipeline",
            synth=pipelines.ShellStep(
                "Synth",
                input=pipelines.CodePipelineSource.connection(
                    self.repository,
                    self.branch,
                    connection_arn=self.gh_connection_arn,
                    trigger_on_push=True
                ),
                commands=[
                    "npm install -g aws-cdk",  # Installs the cdk cli on Codebuild
                    "pip install -r requirements.txt",  # Instructs Codebuild to install required packages
                    "npx cdk synth",
                ]
            ),
        )
        # Deploy to a staging environment
        deploy_staging = MyDjangoAppPipelineStage(
            self, "MyDjangoAppStaging",
            django_settings_module="app.settings.stage",
            django_debug=True,
            domain_name="scalabledjango.com",
            subdomain="stage",
            db_min_capacity=rds.AuroraCapacityUnit.ACU_2,
            db_max_capacity=rds.AuroraCapacityUnit.ACU_2,
            db_auto_pause_minutes=5
        )
        pipeline.add_stage(deploy_staging)
        # Deploy to production after manual approval
        deploy_production = MyDjangoAppPipelineStage(
            self, "MyDjangoAppProduction",
            django_settings_module="app.settings.prod",
            django_debug=False,
            domain_name="scalabledjango.com"
        )
        pipeline.add_stage(
            deploy_production,
            pre=[
                pipelines.ManualApprovalStep("PromoteToProduction")
            ]
        )
