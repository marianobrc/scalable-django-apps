""" Staging Settings """
import json
from socket import gethostname, gethostbyname
from .base import *
from aws_utils import aws_secrets


DEBUG = False
# Set to your Domain here
ALLOWED_HOSTS = [
    "production.domain.com",
]
# The ALB uses the IP while calling the health check endpoint
if os.environ.get("AWS_EXECUTION_ENV"):
    ALLOWED_HOSTS.append(gethostbyname(gethostname()))

print("Loading env vars..")
DB_AWS_SECRET_NAME = os.environ.get("DB_AWS_SECRET_NAME")
DJANGO_SECRET_AWS_SECRET_NAME = os.environ.get("DJANGO_SECRET_AWS_SECRET_NAME")
SECRET_KEY = aws_secrets.get_secret(
    secret_name=DJANGO_SECRET_AWS_SECRET_NAME,
    region_name="us-east-1",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY
)

print("Loading db secrets..")
# Database
# https://docs.djangoproject.com/en/4.0/ref/settings/#databases
db_secrets = json.loads(
    aws_secrets.get_secret(
        secret_name=DB_AWS_SECRET_NAME,
        region_name="us-east-1",
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY
    )
)
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
