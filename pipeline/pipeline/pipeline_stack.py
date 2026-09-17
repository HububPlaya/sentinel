from aws_cdk import Stack
from aws_cdk import aws_codepipeline as codepipeline
from aws_cdk import aws_codepipeline_actions as codepipeline_actions
from constructs import Construct

from .config import TargetRef
from .constructs import ElasticBeanstalkDeployTarget, GitHubSourceAction, TestBuildProject


class PipelineStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        github_owner: str,
        github_repo: str,
        github_branch: str,
        connection_arn: str,
        targets_by_env: dict[str, TargetRef],
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.source = GitHubSourceAction(
            self, "Source",
            connection_arn=connection_arn,
            github_owner=github_owner,
            github_repo=github_repo,
            github_branch=github_branch,
        )

        self.build = TestBuildProject(
            self, "Build",
            target=targets_by_env["dev"],
            input_artifact=self.source.output,
        )

        self.pipeline = codepipeline.Pipeline(
            self, "Pipeline",
            pipeline_name=f"{targets_by_env['dev'].application_name}-app-pipeline",
            stages=[
                codepipeline.StageProps(stage_name="Source", actions=[self.source.action]),
                codepipeline.StageProps(stage_name="Build", actions=[self.build.action]),
            ],
        )

        self._add_deploy_stage("dev", targets_by_env["dev"])
        self._add_deploy_stage("test", targets_by_env["test"])
        self._add_approval_stage("BeforeStage")
        self._add_deploy_stage("stage", targets_by_env["stage"])
        self._add_approval_stage("BeforeProd")
        self._add_deploy_stage("prod", targets_by_env["prod"])

    def _add_deploy_stage(self, env_name: str, target: TargetRef) -> None:
        deploy_target = ElasticBeanstalkDeployTarget(
            self, f"DeployTarget{env_name.capitalize()}",
            application_name=target.application_name,
            environment_name=target.environment_name,
        )
        stage = self.pipeline.add_stage(stage_name=f"Deploy_{env_name}")
        deploy_target.add_deploy_action(stage, self.build.output)

    def _add_approval_stage(self, stage_name: str) -> None:
        self.pipeline.add_stage(stage_name=stage_name).add_action(
            codepipeline_actions.ManualApprovalAction(action_name="Approve")
        )