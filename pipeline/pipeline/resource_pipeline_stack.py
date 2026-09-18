from aws_cdk import Stack
from aws_cdk import aws_codepipeline as codepipeline
from aws_cdk import aws_codepipeline_actions as codepipeline_actions
from constructs import Construct

from .constructs import CdkDeployProject, GitHubSourceAction


class ResourcePipelineStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        github_owner: str,
        github_repo: str,
        github_branch: str,
        connection_arn: str,
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

        self.pipeline = codepipeline.Pipeline(
            self, "Pipeline",
            pipeline_name="infra-resource-pipeline",
            stages=[
                codepipeline.StageProps(stage_name="Source", actions=[self.source.action]),
            ],
        )

        account, region = self.account, self.region

        # dev's deploy also creates the shared Application, once — every other
        # environment only ever deploys its own environment stack.
        self._add_deploy_stage("dev", ["SnackRecommenderApplication", "SnackRecommenderInfra-dev"], account, region)
        self._add_deploy_stage("test", ["SnackRecommenderInfra-test"], account, region)
        self._add_approval_stage("BeforeStage")
        self._add_deploy_stage("stage", ["SnackRecommenderInfra-stage"], account, region)
        self._add_approval_stage("BeforeProd")
        self._add_deploy_stage("prod", ["SnackRecommenderInfra-prod"], account, region)

    def _add_deploy_stage(self, env_name: str, stack_names: list[str], account: str, region: str) -> None:
        deploy = CdkDeployProject(
            self, f"Deploy{env_name.capitalize()}",
            env_name=env_name,
            stack_names=stack_names,
            input_artifact=self.source.output,
            account=account,
            region=region,
        )
        self.pipeline.add_stage(stage_name=f"Deploy_{env_name}").add_action(deploy.action)

    def _add_approval_stage(self, stage_name: str) -> None:
        self.pipeline.add_stage(stage_name=stage_name).add_action(
            codepipeline_actions.ManualApprovalAction(action_name="Approve")
        )