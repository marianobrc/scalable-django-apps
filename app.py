#!/usr/bin/env python3
import os
import aws_cdk as cdk
from aws_cdk import (
    Environment,
)
from my_django_app.pipeline_stack import MyDjangoAppPipelineStack


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
app.synth()
