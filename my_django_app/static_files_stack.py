from aws_cdk import (
    Stack,
    RemovalPolicy,
    aws_s3 as s3,
    aws_cloudfront as cloudfront
)
from constructs import Construct


class StaticFilesStack(Stack):

    def __init__(
            self,
            scope: Construct,
            construct_id: str,
            bucket_name: str = None,
            **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        self.bucket_name = bucket_name

        # Create a private bucket
        self.s3_bucket = s3.Bucket(
            self, f"Bucket",
            bucket_name=bucket_name,  # Bucket name must be globally unique. If not set it's assigned by Cloudformation
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.DESTROY,  # Delete objects on bucket removal
        )

        # Add a CloudFront distribution with a OriginAccessIdentity
        self.oai = cloudfront.OriginAccessIdentity(
            self, f"BucketOAI",
            comment="OAI to access backend static files."
        )
        self.s3_bucket.grant_read(self.oai)
        self.cloudfront_distro = cloudfront.CloudFrontWebDistribution(
            self, f"CloudFrontDistro",
            origin_configs=[
                cloudfront.SourceConfiguration(  # Set the S3 bucket as the source
                    s3_origin_source=cloudfront.S3OriginConfig(
                        s3_bucket_source=self.s3_bucket,
                        origin_access_identity=self.oai
                    ),
                    behaviors=[
                        cloudfront.Behavior(is_default_behavior=True)
                    ],
                )
            ]
        )