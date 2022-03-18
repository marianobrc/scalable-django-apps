#!/usr/bin/env python3
import os
import aws_cdk as cdk
from my_django_app.pipeline_stack import MyDjangoAppPipelineStack


app = cdk.App()
MyDjangoAppPipelineStack(
    app,
    "MyDjangoAppPipeline",
    "marianobrc/scalable-django-apps",
    "master",
    gh_connection_arn=os.getenv('CDK_GH_CONNECTION_ARN')
)
app.synth()
