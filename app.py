#!/usr/bin/env python3
import os
import aws_cdk as cdk
from aws_cdk import (
    Environment,
)
from my_django_app.pipeline_stack import MyDjangoAppPipelineStack
from my_django_app.run_task_stack import RunTaskStack

app = cdk.App()
pipeline = MyDjangoAppPipelineStack(
    app,
    "MyDjangoAppPipeline",
    repository="marianobrc/scalable-django-apps",
    branch="master",
    ssm_gh_connection_param="/github/connection",
    env=Environment(
        account=os.getenv('CDK_DEFAULT_ACCOUNT'),
        region=os.getenv('CDK_DEFAULT_REGION')
    ),
)
run_cmd_in_staging = RunTaskStack(
    app,
    "RunTaskInStaging",
    env=Environment(
        account=os.getenv('CDK_DEFAULT_ACCOUNT'),
        region=os.getenv('CDK_DEFAULT_REGION')
    ),
    stage_name=pipeline.staging_env.stage_name
)
# run_cmd_in_production = RunTaskStack(
#     app,
#     "RunTaskInProduction",
#     env=Environment(
#         account=os.getenv('CDK_DEFAULT_ACCOUNT'),
#         region=os.getenv('CDK_DEFAULT_REGION')
#     ),
#     stage_name=pipeline.production_env.stage_name
# )
app.synth()
