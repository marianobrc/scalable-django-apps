""" Staging Settings """
import json
from socket import gethostname, gethostbyname
from .base import *
from aws_utils import aws_secrets


DEBUG = False
# Set to your Domain here
ALLOWED_HOSTS = [
    "app.stage.domain.com",
]
# The ALB uses the IP while calling the health check endpoint
if os.environ.get("AWS_EXECUTION_ENV"):
    ALLOWED_HOSTS.append(gethostbyname(gethostname()))

print("Loading env vars..")
# AWS Settings
AWS_ACCOUNT_ID = os.getenv("AWS_ACCOUNT_ID")
AWS_REGION_NAME = os.getenv("AWS_REGION_NAME", "us-east-1")
AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")
DB_AWS_SECRET_NAME = os.environ.get("DB_AWS_SECRET_NAME")
DJANGO_SECRET_AWS_SECRET_NAME = os.environ.get("DJANGO_SECRET_AWS_SECRET_NAME")
SECRET_KEY = aws_secrets.get_secret(
    secret_name=DJANGO_SECRET_AWS_SECRET_NAME,
    region_name="us-east-1",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY
)

print("Loading db secrets..")
db_secrets = json.loads(
    aws_secrets.get_secret(
        secret_name=DB_AWS_SECRET_NAME,
        region_name="us-east-1",
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY
    )
)
# Database settings
# https://docs.djangoproject.com/en/4.0/ref/settings/#databases
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": db_secrets["NAME"],
        "USER": db_secrets["USER"],
        "PASSWORD": db_secrets["PASSWORD"],
        "HOST": db_secrets["HOST"],
        "PORT": db_secrets["PORT"],
    }
}

# Static files and Media are stored in S3 and served with CloudFront
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
STATICFILES_STORAGE = 'storages.backends.s3boto3.S3StaticStorage'
AWS_STORAGE_BUCKET_NAME = os.getenv("AWS_STORAGE_BUCKET_NAME")
AWS_S3_CUSTOM_DOMAIN = os.getenv("CLOUDFRONT_URL")
print(f"Static files served from:{AWS_S3_CUSTOM_DOMAIN}")

# Redirects all non-HTTPS requests to HTTPS.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = False  # The TLS connection is terminated at the load balancer
