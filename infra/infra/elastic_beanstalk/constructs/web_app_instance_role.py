from aws_cdk import aws_iam as iam
from constructs import Construct
from infra.elastic_beanstalk.config import IamConfig


class WebAppInstanceRole(Construct):
    def __init__(self, scope: Construct, construct_id: str, *, env_name: str, iam_config: IamConfig) -> None:
        super().__init__(scope, construct_id)

        role_name = f"{iam_config.role_name}-{env_name}"
        profile_name = f"{iam_config.instance_profile_name}-{env_name}"

        self.role = iam.Role(
            self, "Role",
            role_name=role_name,
            assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "AWSElasticBeanstalkWebTier"
                ),
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "AWSElasticBeanstalkMulticontainerDocker"
                ),
            ],
        )

        self.instance_profile = iam.CfnInstanceProfile(
            self, "InstanceProfile",
            instance_profile_name=profile_name,
            roles=[self.role.role_name],
        )