import json

import aws_cdk as core
import aws_cdk.assertions as assertions
from aws_cdk import aws_codepipeline as codepipeline

from pipeline.config import TARGETS
from pipeline.constructs import TestBuildProject


def _build_template():
    app = core.App()
    stack = core.Stack(app, "TestStack", env=core.Environment(account="123456789012", region="us-east-1"))
    construct = TestBuildProject(
        stack, "Build",
        target=TARGETS[("snack-recommender", "dev")],
        input_artifact=codepipeline.Artifact("SourceOutput"),
        codeartifact_domain="sentinel-platform",
        codeartifact_repository="platform-packages",
        account=stack.account,
        region=stack.region,
    )
    template = assertions.Template.from_stack(stack)
    return template, construct


def _buildspec():
    template, _ = _build_template()
    [project] = template.find_resources("AWS::CodeBuild::Project").values()
    return json.loads(project["Properties"]["Source"]["BuildSpec"])


def test_install_phase_logs_into_codeartifact_for_pip():
    buildspec = _buildspec()
    install_commands = buildspec["phases"]["install"]["commands"]
    assert any("codeartifact login --tool pip" in c for c in install_commands)


def test_build_phase_publishes_platform_core_before_snack_recommender_installs():
    buildspec = _buildspec()
    build_commands = buildspec["phases"]["build"]["commands"]
    joined = "\n".join(build_commands)

    publish_index = next(i for i, c in enumerate(build_commands) if "twine upload" in c or "ALREADY_PUBLISHED" in c)
    install_indices = [i for i, c in enumerate(build_commands) if "requirements-dev.txt" in c]
    assert len(install_indices) == 2, "expected exactly one install for platform_core and one for snack-recommender"
    snack_install_index = install_indices[-1]
    assert "codeartifact login --tool twine" in joined
    assert publish_index < snack_install_index


def test_grants_codeartifact_read_and_publish_permissions():
    template, _ = _build_template()
    template.has_resource_properties("AWS::IAM::Policy", assertions.Match.object_like({
        "PolicyDocument": assertions.Match.object_like({
            "Statement": assertions.Match.array_with([
                assertions.Match.object_like({
                    "Action": assertions.Match.array_with(["codeartifact:PublishPackageVersion"]),
                }),
            ]),
        }),
    }))


def test_codeartifact_grants_use_correct_resource_type_per_action():
    # GetAuthorizationToken is domain-level, GetRepositoryEndpoint is repository-level, and the
    # per-package actions need a package-level ARN -- mixing these up is an exit-254 CodeBuild
    # failure at `aws codeartifact login`, not a synth-time error, so this is worth pinning down.
    template, _ = _build_template()
    [policy] = [
        p for p in template.find_resources("AWS::IAM::Policy").values()
        if any(
            "codeartifact:GetAuthorizationToken" in (s.get("Action") if isinstance(s.get("Action"), list) else [s.get("Action")])
            for s in p["Properties"]["PolicyDocument"]["Statement"]
        )
    ]
    statements = policy["Properties"]["PolicyDocument"]["Statement"]

    def resource_for(action):
        for s in statements:
            actions = s["Action"] if isinstance(s["Action"], list) else [s["Action"]]
            if action in actions:
                resources = s["Resource"] if isinstance(s["Resource"], list) else [s["Resource"]]
                return resources
        raise AssertionError(f"no statement grants {action}")

    assert any(":domain/" in r for r in resource_for("codeartifact:GetAuthorizationToken"))
    assert any(":repository/" in r for r in resource_for("codeartifact:GetRepositoryEndpoint"))
    assert any(":package/" in r for r in resource_for("codeartifact:ReadFromRepository"))
    assert any(":package/" in r for r in resource_for("codeartifact:PublishPackageVersion"))


def test_grants_sts_service_bearer_token_for_codeartifact():
    template, _ = _build_template()
    template.has_resource_properties("AWS::IAM::Policy", assertions.Match.object_like({
        "PolicyDocument": assertions.Match.object_like({
            "Statement": assertions.Match.array_with([
                assertions.Match.object_like({
                    "Action": "sts:GetServiceBearerToken",
                    "Condition": {"StringEquals": {"sts:AWSServiceName": "codeartifact.amazonaws.com"}},
                }),
            ]),
        }),
    }))
