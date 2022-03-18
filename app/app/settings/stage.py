""" Staging Settings """
from socket import gethostname, gethostbyname
from .base import *

DEBUG = False
# Set to your Domain here
ALLOWED_HOSTS = [
    "stg.scalabledjango.com",
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
