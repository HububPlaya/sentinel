from aws_cdk import aws_elasticbeanstalk as eb
from constructs import Construct
from infra.elastic_beanstalk.config import EnvConfig


class WebAppHosting(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        app_name: str,
        env_config: EnvConfig,
        instance_profile_name: str,
        version_label: str | None = None,
    ) -> None:
        super().__init__(scope, construct_id)

        self.application = self._create_application(app_name)
        self.environment = self._create_environment(app_name, env_config, instance_profile_name, version_label)
        self.environment.add_resource_dependency(self.application)

    def _create_application(self, app_name: str) -> eb.CfnApplication:
        return eb.CfnApplication(self, "Application", application_name=app_name)

    def _create_environment(
        self, app_name: str, cfg: EnvConfig, instance_profile_name: str, version_label: str | None
    ) -> eb.CfnEnvironment:
        return eb.CfnEnvironment(
            self, "Environment",
            application_name=app_name,
            environment_name=f"{app_name}-{cfg.env_name}",
            solution_stack_name="64bit Amazon Linux 2023 v4.13.8 running Python 3.13",
            version_label=version_label,
            option_settings=[
                eb.CfnEnvironment.OptionSettingProperty(
                    namespace="aws:autoscaling:launchconfiguration",
                    option_name="IamInstanceProfile",
                    value=instance_profile_name,
                ),
                eb.CfnEnvironment.OptionSettingProperty(
                    namespace="aws:autoscaling:launchconfiguration",
                    option_name="InstanceType",
                    value=cfg.instance.instance_type,
                ),
                eb.CfnEnvironment.OptionSettingProperty(
                    namespace="aws:autoscaling:asg",
                    option_name="MinSize",
                    value=str(cfg.scaling.min_instances),
                ),
                eb.CfnEnvironment.OptionSettingProperty(
                    namespace="aws:autoscaling:asg",
                    option_name="MaxSize",
                    value=str(cfg.scaling.max_instances),
                ),
            ],
        )