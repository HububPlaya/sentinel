#!/usr/bin/env python3
import os

import aws_cdk as cdk

from pipeline.config import TARGETS
from pipeline.pipeline_stack import PipelineStack
from pipeline.resource_pipeline_stack import ResourcePipelineStack

app = cdk.App()

GITHUB_OWNER = "HububPlaya"
GITHUB_REPO = "sentinel"
GITHUB_BRANCH = "main"
EXISTING_CONNECTION_ARN = "arn:aws:codestar-connections:us-east-1:976193251729:connection/9ee748a7-26a4-4849-aa0c-5a89e9cda8af"

targets_by_env = {
    env: TARGETS[("snack-recommender", env)]
    for env in ("dev", "test", "stage", "prod")
}

PipelineStack(
    app, "PipelineStack-snack-recommender",
    github_owner=GITHUB_OWNER,
    github_repo=GITHUB_REPO,
    github_branch=GITHUB_BRANCH,
    connection_arn=EXISTING_CONNECTION_ARN,
    targets_by_env=targets_by_env,
    env=cdk.Environment(
        account=os.getenv("CDK_DEFAULT_ACCOUNT"),
        region=os.getenv("CDK_DEFAULT_REGION"),
    ),
)

ResourcePipelineStack(
    app, "ResourcePipelineStack",
    github_owner=GITHUB_OWNER,
    github_repo=GITHUB_REPO,
    github_branch=GITHUB_BRANCH,
    connection_arn=EXISTING_CONNECTION_ARN,
    env=cdk.Environment(
        account=os.getenv("CDK_DEFAULT_ACCOUNT"),
        region=os.getenv("CDK_DEFAULT_REGION"),
    ),
)

app.synth()