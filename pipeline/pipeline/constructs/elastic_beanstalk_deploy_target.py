from aws_cdk import aws_codepipeline as codepipeline
from aws_cdk import aws_codepipeline_actions as codepipeline_actions
from constructs import Construct

from .deploy_target import DeployTarget


class ElasticBeanstalkDeployTarget(Construct):
    """Deploys to an existing Elastic Beanstalk Application/Environment.

    Targets resources by name only — it has no dependency on infra/'s CDK stack, since
    application_name/environment_name are plain values chosen at authoring time, not
    CloudFormation-generated tokens. See infra/infra/elastic_beanstalk/ for what actually
    creates the Application/Environment this targets.
    """

    def __init__(
        self, scope: Construct, construct_id: str, *, application_name: str, environment_name: str
    ) -> None:
        super().__init__(scope, construct_id)
        self.application_name = application_name
        self.environment_name = environment_name

    def add_deploy_action(
        self,
        stage: codepipeline.IStage,
        input_artifact: codepipeline.Artifact,
        run_order: int = 1,
    ) -> None:
        stage.add_action(
            codepipeline_actions.ElasticBeanstalkDeployAction(
                action_name="DeployToElasticBeanstalk",
                application_name=self.application_name,
                environment_name=self.environment_name,
                input=input_artifact,
                run_order=run_order,
            )
        )