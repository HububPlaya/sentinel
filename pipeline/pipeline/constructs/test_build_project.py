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
                            # platform_core has no dedicated pipeline/target of its own yet,
                            # so its suite (with its own --cov-fail-under gate) runs here,
                            # since this target depends on it. Revisit if/when platform_core
                            # gets a real target -- this will otherwise re-run once per
                            # snack-recommender environment stage.
                            "cd $CODEBUILD_SRC_DIR/platform_core",
                            "pip install -r requirements-dev.txt",
                            "python -m pytest",
                            f"cd $CODEBUILD_SRC_DIR/{target.source_path}",
                            "python -m pytest",
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