import aws_cdk as core
import aws_cdk.assertions as assertions

from infra.codeartifact.codeartifact_stack import CodeArtifactStack


def test_domain_created():
    app = core.App()
    stack = CodeArtifactStack(app, "CodeArtifact")
    template = assertions.Template.from_stack(stack)

    template.has_resource_properties("AWS::CodeArtifact::Domain", {
        "DomainName": CodeArtifactStack.DOMAIN_NAME,
    })


def test_repository_created_with_public_pypi_connection():
    app = core.App()
    stack = CodeArtifactStack(app, "CodeArtifact")
    template = assertions.Template.from_stack(stack)

    template.has_resource_properties("AWS::CodeArtifact::Repository", {
        "RepositoryName": CodeArtifactStack.REPOSITORY_NAME,
        "ExternalConnections": ["public:pypi"],
    })
