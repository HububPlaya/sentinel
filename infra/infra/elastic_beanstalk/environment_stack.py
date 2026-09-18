from aws_cdk import Stack
from aws_cdk import aws_ec2 as ec2
from constructs import Construct

from infra.elastic_beanstalk.config import EnvConfig
from infra.elastic_beanstalk.constructs import ElasticBeanstalkEnvironment, ElasticBeanstalkInstanceRole


class EnvironmentStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        app_name: str,
        env_config: EnvConfig,
        security_group: ec2.ISecurityGroup,
        app_environment_variables: dict[str, str] | None = None,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.vpc = ec2.Vpc.from_lookup(self, "Vpc", is_default=True)
        self.security_group = security_group

        self.instance_role = ElasticBeanstalkInstanceRole(
            self, "InstanceRole",
            app_name=app_name, env_name=env_config.env_name, iam_config=env_config.iam,
        )

        self.eb_environment = ElasticBeanstalkEnvironment(
            self, "Environment",
            app_name=app_name, env_config=env_config,
            instance_profile_name=self.instance_role.instance_profile.ref,
            security_group_id=self.security_group.security_group_id,
            vpc=self.vpc,
            app_environment_variables=app_environment_variables,
        )