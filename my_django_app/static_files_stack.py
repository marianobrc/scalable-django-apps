import typing
from aws_cdk import (
    Stack,
    RemovalPolicy,
    aws_s3 as s3,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as origins,
)
from constructs import Construct


class StaticFilesStack(Stack):

    def __init__(
            self,
            scope: Construct,
            construct_id: str,
            bucket_name: str = None,
            cors_allowed_origins: typing.Sequence[str] = None,
            **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        self.bucket_name = bucket_name
        self.cors_allowed_origins = cors_allowed_origins
        # Create a private bucket
        self.s3_bucket = s3.Bucket(
            self, f"Bucket",
            bucket_name=bucket_name,  # Bucket name must be globally unique. If not set it's assigned by Cloudformation
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.DESTROY,  # Delete objects on bucket removal
            auto_delete_objects=True
        )
        # Add an OriginAccessIdentity to access the bucket
        self.oai = cloudfront.OriginAccessIdentity(
            self, f"BucketOAI",
            comment="OAI to access backend static files."
        )
        self.s3_bucket.grant_read(self.oai)
        # Prepare CORS settings
        if self.cors_allowed_origins:
            response_headers_policy = cloudfront.ResponseHeadersPolicy(
                self, "ResponseHeadersPolicy",
                comment="CORS policy",
                cors_behavior=cloudfront.ResponseHeadersCorsBehavior(
                    access_control_allow_credentials=True,
                    access_control_allow_headers=[
                        "accept",
                        "accept-encoding",
                        "authorization",
                        "content-type",
                        "dnt",
                        "origin",
                        "user-agent",
                        "x-csrftoken"
                    ],
                    access_control_allow_methods=["GET", "HEAD", "OPTIONS"],
                    access_control_allow_origins=cors_allowed_origins,
                    origin_override=True
                )
            )
        else:
            response_headers_policy = cloudfront.ResponseHeadersPolicy.CORS_ALLOW_ALL_ORIGINS
        # Create the cloudfront distribution
        self.cloudfront_distro = cloudfront.Distribution(
            self, "CFDistribution",
            default_behavior=cloudfront.BehaviorOptions(
                origin=origins.S3Origin(
                    self.s3_bucket,
                    origin_access_identity=self.oai
                ),
                response_headers_policy=response_headers_policy
            )
        )
