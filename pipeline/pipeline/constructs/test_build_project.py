from aws_cdk import aws_codebuild as codebuild
from aws_cdk import aws_codepipeline as codepipeline
from aws_cdk import aws_codepipeline_actions as codepipeline_actions
from constructs import Construct

from ..config import TargetRef


class TestBuildProject(Construct):
    def __init__(
        self, scope: Construct, construct_id: str, *, target: TargetRef, input_artifact: codepipeline.Artifact
    ) -> None:
        super().__init__(scope, construct_id)

        self.output = codepipeline.Artifact("BuildOutput")

        self.project = codebuild.PipelineProject(
            self, "Project",
            build_spec=codebuild.BuildSpec.from_object({
                "version": "0.2",
                "phases": {
                    "install": {
                        "runtime-versions": {"python": "3.13"},
                        "commands": [
                            f"cd $CODEBUILD_SRC_DIR/{target.source_path}",
                            "pip install -r requirements-dev.txt",
                        ],
                    },
                    "build": {
                        "commands": [
                            f"cd $CODEBUILD_SRC_DIR/{target.source_path}",
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

        self.action = codepipeline_actions.CodeBuildAction(
            action_name="Build_And_Test",
            project=self.project,
            input=input_artifact,
            outputs=[self.output],
        )