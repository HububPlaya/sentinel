from aws_cdk import aws_codebuild as codebuild
from aws_cdk import aws_codepipeline as codepipeline
from aws_cdk import aws_codepipeline_actions as codepipeline_actions
from aws_cdk import aws_iam as iam
from constructs import Construct

from ..config import TargetRef


class TestBuildProject(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        target: TargetRef,
        input_artifact: codepipeline.Artifact,
        codeartifact_domain: str,
        codeartifact_repository: str,
        account: str,
        region: str,
    ) -> None:
        super().__init__(scope, construct_id)

        self.output = codepipeline.Artifact("BuildOutput")

        codeartifact_login = (
            f"aws codeartifact login --tool pip --domain {codeartifact_domain} "
            f"--domain-owner {account} --repository {codeartifact_repository} --region {region}"
        )
        codeartifact_twine_login = (
            f"aws codeartifact login --tool twine --domain {codeartifact_domain} "
            f"--domain-owner {account} --repository {codeartifact_repository} --region {region}"
        )
        list_published_versions = (
            f"aws codeartifact list-package-versions --domain {codeartifact_domain} "
            f"--domain-owner {account} --repository {codeartifact_repository} --format pypi "
            f"--package platform-core --region {region} "
            '--query "length(versions[?version==\'$PLATFORM_CORE_VERSION\'])" --output text'
        )

        self.project = codebuild.PipelineProject(
            self, "Project",
            build_spec=codebuild.BuildSpec.from_object({
                "version": "0.2",
                "phases": {
                    "install": {
                        "runtime-versions": {"python": "3.13"},
                        "commands": [
                            # Primes pip so both platform_core's own public-dep install below and
                            # snack-recommender's later resolution of platform_core itself go
                            # through one CodeArtifact-backed index (it proxies public PyPI too).
                            codeartifact_login,
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
                            # Publish whatever version platform_core/pyproject.toml currently
                            # declares -- idempotent (skipped if already published), so a version
                            # bump there is the deliberate signal a new release is ready, not a
                            # separate manual publish step.
                            "PLATFORM_CORE_VERSION=$(python -c \"import tomllib; "
                            "print(tomllib.load(open('pyproject.toml','rb'))['project']['version'])\")",
                            "pip install build twine",
                            "python -m build",
                            codeartifact_twine_login,
                            f'ALREADY_PUBLISHED=$({list_published_versions} 2>/dev/null || echo 0)',
                            'if [ "$ALREADY_PUBLISHED" = "0" ]; then twine upload --repository codeartifact dist/*; '
                            'else echo "platform_core==$PLATFORM_CORE_VERSION already published, skipping"; fi',
                            f"cd $CODEBUILD_SRC_DIR/{target.source_path}",
                            "pip install -r requirements-dev.txt",
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

        # CodeArtifact IAM actions split by resource type: GetAuthorizationToken is domain-level,
        # GetRepositoryEndpoint is repository-level, and the per-package read/publish actions
        # below need a package-level ARN -- a repository or domain ARN won't satisfy them even
        # though it reads like it should.
        self.project.add_to_role_policy(
            self._codeartifact_policy_statement(
                actions=["codeartifact:GetAuthorizationToken"],
                account=account, region=region,
                resource_segment=f"domain/{codeartifact_domain}",
            )
        )
        self.project.add_to_role_policy(
            self._codeartifact_policy_statement(
                actions=["codeartifact:GetRepositoryEndpoint"],
                account=account, region=region,
                resource_segment=f"repository/{codeartifact_domain}/{codeartifact_repository}",
            )
        )
        self.project.add_to_role_policy(
            self._codeartifact_policy_statement(
                actions=[
                    "codeartifact:ReadFromRepository",
                    "codeartifact:PublishPackageVersion",
                    "codeartifact:PutPackageMetadata",
                ],
                account=account, region=region,
                resource_segment=f"package/{codeartifact_domain}/{codeartifact_repository}/*/*/*",
            )
        )
        self.project.add_to_role_policy(
            self._sts_bearer_token_policy_statement()
        )

        self.action = codepipeline_actions.CodeBuildAction(
            action_name="Build_And_Test",
            project=self.project,
            input=input_artifact,
            outputs=[self.output],
        )

    @staticmethod
    def _codeartifact_policy_statement(*, actions, account, region, resource_segment):
        return iam.PolicyStatement(
            actions=actions,
            resources=[f"arn:aws:codeartifact:{region}:{account}:{resource_segment}"],
        )

    @staticmethod
    def _sts_bearer_token_policy_statement():
        return iam.PolicyStatement(
            actions=["sts:GetServiceBearerToken"],
            resources=["*"],
            conditions={"StringEquals": {"sts:AWSServiceName": "codeartifact.amazonaws.com"}},
        )
