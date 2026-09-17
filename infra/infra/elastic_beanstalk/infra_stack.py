from aws_cdk import Stack
from constructs import Construct

from infra.elastic_beanstalk.config import EnvConfig
from infra.elastic_beanstalk.constructs import AppBundle, WebAppHosting, WebAppInstanceRole


class InfraStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        app_name: str,
        env_config: EnvConfig,
        app_source_path: str,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.instance_role = WebAppInstanceRole(
            self, "WebAppInstanceRole",
            app_name=app_name,
            env_name=env_config.env_name,
            iam_config=env_config.iam,
        )

        self.app_bundle = AppBundle(
            self, "AppBundle",
            app_name=app_name,
            source_path=app_source_path,
        )

        self.web_app_hosting = WebAppHosting(
            self, "WebAppHosting",
            app_name=app_name,
            env_config=env_config,
            instance_profile_name=self.instance_role.instance_profile.ref,
            version_label=self.app_bundle.application_version.ref,
        )

        self.app_bundle.application_version.add_resource_dependency(
            self.web_app_hosting.application
        )