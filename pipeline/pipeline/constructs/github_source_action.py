from aws_cdk import aws_codepipeline as codepipeline
from aws_cdk import aws_codepipeline_actions as codepipeline_actions
from constructs import Construct


class GitHubSourceAction(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        connection_arn: str,
        github_owner: str,
        github_repo: str,
        github_branch: str,
    ) -> None:
        super().__init__(scope, construct_id)

        self.output = codepipeline.Artifact("SourceOutput")

        self.action = codepipeline_actions.CodeStarConnectionsSourceAction(
            action_name="GitHub_Source",
            owner=github_owner,
            repo=github_repo,
            branch=github_branch,
            connection_arn=connection_arn,
            output=self.output,
        )