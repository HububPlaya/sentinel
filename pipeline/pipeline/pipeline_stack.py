from aws_cdk import Stack
from aws_cdk import aws_codebuild as codebuild
from aws_cdk import aws_codepipeline as codepipeline
from aws_cdk import aws_codepipeline_actions as codepipeline_actions
from aws_cdk import aws_codestarconnections as codestarconnections
from constructs import Construct

from .config import TargetRef
from .constructs import ElasticBeanstalkDeployTarget


class PipelineStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        github_owner: str,
        github_repo: str,
        github_branch: str,
        target: TargetRef,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # One-time manual step after first `cdk deploy`: go to the AWS Console ->
        # Developer Tools -> Settings -> Connections, find this connection in
        # "Pending" status, and click "Update pending connection" to complete the
        # GitHub OAuth handshake. CDK cannot do this step for you.
        self.github_connection = codestarconnections.CfnConnection(
            self, "GitHubConnection",
            connection_name=f"{github_repo}-connection",
            provider_type="GitHub",
        )

        source_output = codepipeline.Artifact("SourceOutput")
        build_output = codepipeline.Artifact("BuildOutput")

        source_action = codepipeline_actions.CodeStarConnectionsSourceAction(
            action_name="GitHub_Source",
            owner=github_owner,
            repo=github_repo,
            branch=github_branch,
            connection_arn=self.github_connection.attr_connection_arn,
            output=source_output,
        )

        build_project = codebuild.PipelineProject(
            self, "BuildProject",
            build_spec=codebuild.BuildSpec.from_object({
                "version": "0.2",
                "phases": {
                    "install": {
                        "runtime-versions": {"python": "3.13"},
                        "commands": [
                            f"cd {target.source_path}",
                            "pip install -r requirements-dev.txt",
                        ],
                    },
                    "build": {
                        "commands": [
                            f"cd {target.source_path}",
                            "echo 'No automated tests yet — placeholder build stage'",
                        ],
                    },
                },
                "artifacts": {
                    "base-directory": target.source_path,
                    "files": ["**/*"],
                },
            }),
        )

        build_action = codepipeline_actions.CodeBuildAction(
            action_name="Build_And_Test",
            project=build_project,
            input=source_output,
            outputs=[build_output],
        )

        deploy_target = ElasticBeanstalkDeployTarget(
            self, "DeployTarget",
            application_name=target.application_name,
            environment_name=target.environment_name,
        )

        pipeline = codepipeline.Pipeline(
            self, "Pipeline",
            pipeline_name=f"{target.environment_name}-pipeline",
            stages=[
                codepipeline.StageProps(stage_name="Source", actions=[source_action]),
                codepipeline.StageProps(stage_name="Build", actions=[build_action]),
            ],
        )

        deploy_stage = pipeline.add_stage(stage_name="Deploy")
        deploy_target.add_deploy_action(deploy_stage, build_output)