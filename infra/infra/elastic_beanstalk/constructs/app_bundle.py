from aws_cdk import aws_elasticbeanstalk as eb
from aws_cdk import aws_iam as iam
from aws_cdk.aws_s3_assets import Asset
from constructs import Construct


class AppBundle(Construct):
    def __init__(self, scope: Construct, construct_id: str, *, app_name: str, source_path: str) -> None:
        super().__init__(scope, construct_id)

        self.asset = Asset(self, "Asset", path=source_path)

        # Elastic Beanstalk's backend needs to read the bundle from S3 itself, separately
        # from the permissions CloudFormation already has to deploy the asset.
        self.asset.grant_read(iam.ServicePrincipal("elasticbeanstalk.amazonaws.com"))

        self.application_version = eb.CfnApplicationVersion(
            self, "ApplicationVersion",
            application_name=app_name,
            source_bundle=eb.CfnApplicationVersion.SourceBundleProperty(
                s3_bucket=self.asset.s3_bucket_name,
                s3_key=self.asset.s3_object_key,
            ),
        )