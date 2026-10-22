from aws_cdk import Stack
from aws_cdk import aws_codeartifact as codeartifact
from constructs import Construct


class CodeArtifactStack(Stack):
    """One shared private package repository for every app the platform hosts.

    Not per-app or per-environment -- platform_core (and any future shared package) is published
    here once and consumed by every onboarded app's deploy, instead of each app vendoring a copy.
    The `public:pypi` external connection means this same repository also transparently proxies
    public packages, so consumers only ever need one index URL.
    """

    DOMAIN_NAME = "sentinel-platform"
    REPOSITORY_NAME = "platform-packages"

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.domain = codeartifact.CfnDomain(
            self, "Domain",
            domain_name=self.DOMAIN_NAME,
        )

        self.repository = codeartifact.CfnRepository(
            self, "Repository",
            repository_name=self.REPOSITORY_NAME,
            domain_name=self.domain.domain_name,
            external_connections=["public:pypi"],
        )
        self.repository.add_dependency(self.domain)

        self.repository_arn = self.repository.attr_arn
        self.domain_name = self.domain.domain_name
        self.repository_name = self.repository.repository_name
