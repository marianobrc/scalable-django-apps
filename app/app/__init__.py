# Override aws endpoints used by boto3 due to issue https://github.com/boto/boto3/issues/1900#issuecomment-873597264
# We import it here to make sure it's imported before boto3
import awsserviceendpoints
import boto3
# This will make sure the app is always imported when
# Django starts so that shared_task will use this app.
from .celery import app as celery_app

__all__ = ('celery_app',)
