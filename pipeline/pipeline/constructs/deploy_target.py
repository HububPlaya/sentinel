from typing import Protocol

from aws_cdk import aws_codepipeline as codepipeline


class DeployTarget(Protocol):
    """Anything the pipeline can ship an artifact to.

    The pipeline construct depends only on this interface, never on a specific service
    (Elastic Beanstalk, Lambda, etc.) — new deploy targets are added by writing a new
    implementation of this Protocol, not by branching inside the pipeline itself.
    """

    def add_deploy_action(
        self,
        stage: codepipeline.IStage,
        input_artifact: codepipeline.Artifact,
        run_order: int = 1,
    ) -> None: ...