""" Staging Settings """
from socket import gethostname, gethostbyname
from .base import *

DEBUG = strtobool(os.getenv("DJANGO_DEBUG", "False"))
# Set to your Domain here
ALLOWED_HOSTS = [
    "stage.scalabledjango.com",
]
# The ALB uses the IP while calling the health check endpoint
if os.environ.get("AWS_EXECUTION_ENV"):
    ALLOWED_HOSTS.append(gethostbyname(gethostname()))

print("Loading env vars..")
# AWS Settings
AWS_ACCOUNT_ID = os.getenv("AWS_ACCOUNT_ID")
AWS_REGION_NAME = os.getenv("AWS_REGION_NAME")
AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")

# Static files and Media are stored in S3 and served with CloudFront
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
STATICFILES_STORAGE = 'storages.backends.s3boto3.S3StaticStorage'
AWS_STORAGE_BUCKET_NAME = os.getenv("AWS_STATIC_FILES_BUCKET_NAME")
AWS_S3_CUSTOM_DOMAIN = os.getenv("AWS_STATIC_FILES_CLOUDFRONT_URL")
print(f"Static files served from:{AWS_S3_CUSTOM_DOMAIN}")

# Redirects all non-HTTPS requests to HTTPS.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = False  # The TLS connection is terminated at the load balancer

# Override celery settings for SQS when running in AWS
CELERY_BROKER_URL = "sqs://"  # Let celery get credentials from env vars or from queue settings
SQS_DEFAULT_QUEUE_URL = os.getenv("SQS_DEFAULT_QUEUE_URL")
CELERY_TASK_DEFAULT_QUEUE = SQS_DEFAULT_QUEUE_URL.split('/')[-1]  # Get the queue name
CELERY_BROKER_TRANSPORT_OPTIONS = {
    "region": AWS_REGION_NAME,
    "visibility_timeout": 3600,
    "polling_interval": 5,
    'predefined_queues': {  # We use an SQS queue created previously with CDK
        CELERY_TASK_DEFAULT_QUEUE: {
            'url': SQS_DEFAULT_QUEUE_URL,  # Important: Set the queue URL with https:// here when using VPC endpoints
            # 'access_key_id': AWS_ACCESS_KEY_ID,
            # 'secret_access_key': AWS_SECRET_ACCESS_KEY,
        }
    }
}