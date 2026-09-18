from aws_cdk import Stack
from constructs import Construct

from infra.elastic_beanstalk.config import EnvConfig
from infra.elastic_beanstalk.constructs import ElasticBeanstalkEnvironment, WebAppInstanceRole


class EnvironmentStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        app_name: str,
        env_config: EnvConfig,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.instance_role = WebAppInstanceRole(
            self, "WebAppInstanceRole",
            app_name=app_name,
            env_name=env_config.env_name,
            iam_config=env_config.iam,
        )

        self.eb_environment = ElasticBeanstalkEnvironment(
            self, "Environment",
            app_name=app_name,
            env_config=env_config,
            instance_profile_name=self.instance_role.instance_profile.ref,
        )