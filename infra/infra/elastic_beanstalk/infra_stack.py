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
            instance_profile_name=self.instance_role.instance_profile.instance_profile_name,
            version_label=self.app_bundle.application_version.ref,
        )

        # Explicit dependency: application_name matching by string doesn't tell CloudFormation
        # these are related — without this, CFN can create both in parallel and fail, since
        # the ApplicationVersion needs the Application to exist first.
        self.app_bundle.application_version.add_resource_dependency(
            self.web_app_hosting.application
        )