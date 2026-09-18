from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_elasticbeanstalk as eb
from constructs import Construct
from infra.elastic_beanstalk.config import EnvConfig


class ElasticBeanstalkEnvironment(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        app_name: str,
        env_config: EnvConfig,
        instance_profile_name: str,
        security_group_id: str,
        vpc: ec2.IVpc,
        version_label: str | None = None,
        app_environment_variables: dict[str, str] | None = None,
    ) -> None:
        super().__init__(scope, construct_id)
        self.environment = self._create_environment(
            app_name, env_config, instance_profile_name, security_group_id,
            vpc, version_label, app_environment_variables or {},
        )

    def _create_environment(
        self, app_name, cfg, instance_profile_name, security_group_id, vpc, version_label, app_environment_variables,
    ) -> eb.CfnEnvironment:
        # Explicit AZ selection from cfg -- us-east-1e in this account doesn't
        # support t3 instance types (confirmed by a real deploy failure). AWS
        # randomizes each account's AZ name-to-physical mapping, so this is
        # account-specific, not universal.
        selected = vpc.select_subnets(
            subnet_type=ec2.SubnetType.PUBLIC,
            availability_zones=cfg.availability_zones,
        )
        subnet_ids = selected.subnet_ids

        option_settings = [
            eb.CfnEnvironment.OptionSettingProperty(
                namespace="aws:ec2:vpc", option_name="VPCId", value=vpc.vpc_id,
            ),
            eb.CfnEnvironment.OptionSettingProperty(
                namespace="aws:ec2:vpc", option_name="Subnets", value=",".join(subnet_ids),
            ),
            eb.CfnEnvironment.OptionSettingProperty(
                namespace="aws:ec2:vpc", option_name="ELBSubnets", value=",".join(subnet_ids),
            ),
            eb.CfnEnvironment.OptionSettingProperty(
                namespace="aws:autoscaling:launchconfiguration",
                option_name="IamInstanceProfile", value=instance_profile_name,
            ),
            eb.CfnEnvironment.OptionSettingProperty(
                namespace="aws:autoscaling:launchconfiguration",
                option_name="InstanceType", value=cfg.instance.instance_type,
            ),
            eb.CfnEnvironment.OptionSettingProperty(
                namespace="aws:autoscaling:launchconfiguration",
                option_name="SecurityGroups", value=security_group_id,
            ),
            eb.CfnEnvironment.OptionSettingProperty(
                namespace="aws:autoscaling:asg", option_name="MinSize", value=str(cfg.scaling.min_instances),
            ),
            eb.CfnEnvironment.OptionSettingProperty(
                namespace="aws:autoscaling:asg", option_name="MaxSize", value=str(cfg.scaling.max_instances),
            ),
        ]

        for key, value in app_environment_variables.items():
            option_settings.append(
                eb.CfnEnvironment.OptionSettingProperty(
                    namespace="aws:elasticbeanstalk:application:environment",
                    option_name=key, value=value,
                )
            )

        return eb.CfnEnvironment(
            self, "Environment",
            application_name=app_name,
            environment_name=f"{app_name}-{cfg.env_name}",
            solution_stack_name="64bit Amazon Linux 2023 v4.13.8 running Python 3.13",
            version_label=version_label,
            option_settings=option_settings,
        )