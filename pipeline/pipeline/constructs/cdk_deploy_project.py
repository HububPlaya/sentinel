from aws_cdk import aws_codebuild as codebuild
from aws_cdk import aws_codepipeline as codepipeline
from aws_cdk import aws_codepipeline_actions as codepipeline_actions
from aws_cdk import aws_iam as iam
from constructs import Construct


class CdkDeployProject(Construct):
    BOOTSTRAP_QUALIFIER = "hnb659fds"

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        env_name: str,
        stack_names: list[str],
        input_artifact: codepipeline.Artifact,
        account: str,
        region: str,
    ) -> None:
        super().__init__(scope, construct_id)

        stacks_arg = " ".join(stack_names)

        self.project = codebuild.PipelineProject(
            self, "Project",
            build_spec=codebuild.BuildSpec.from_object({
                "version": "0.2",
                "phases": {
                    "install": {
                        "runtime-versions": {"python": "3.13", "nodejs": "20"},
                        "commands": [
                            "npm install -g aws-cdk",
                            "cd $CODEBUILD_SRC_DIR/infra",
                            "pip install -r requirements.txt",
                        ],
                    },
                    "build": {
                        "commands": [
                            "cd $CODEBUILD_SRC_DIR/infra",
                            f"cdk deploy {stacks_arg} -c env={env_name} --require-approval never",
                        ],
                    },
                },
            }),
        )

        bootstrap_role_arns = [
            f"arn:aws:iam::{account}:role/cdk-{self.BOOTSTRAP_QUALIFIER}-deploy-role-{account}-{region}",
            f"arn:aws:iam::{account}:role/cdk-{self.BOOTSTRAP_QUALIFIER}-file-publishing-role-{account}-{region}",
            f"arn:aws:iam::{account}:role/cdk-{self.BOOTSTRAP_QUALIFIER}-image-publishing-role-{account}-{region}",
            f"arn:aws:iam::{account}:role/cdk-{self.BOOTSTRAP_QUALIFIER}-lookup-role-{account}-{region}",
        ]
        self.project.add_to_role_policy(
            iam.PolicyStatement(actions=["sts:AssumeRole"], resources=bootstrap_role_arns)
        )

        self.action = codepipeline_actions.CodeBuildAction(
            action_name=f"Deploy_{env_name}",
            project=self.project,
            input=input_artifact,
        )