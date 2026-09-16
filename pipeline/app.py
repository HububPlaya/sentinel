#!/usr/bin/env python3
import os

import aws_cdk as cdk

from pipeline.config import TARGETS
from pipeline.pipeline_stack import PipelineStack

app = cdk.App()

# TODO: replace with your actual GitHub username/org and repo name
GITHUB_OWNER = "HububPlaya"
GITHUB_REPO = "sentinel"
GITHUB_BRANCH = "feature/cf-template-elastic-beanstalk"

target = TARGETS[("snack-recommender", "dev")]

PipelineStack(
    app, f"PipelineStack-{target.application_name}-{target.environment_name}",
    github_owner=GITHUB_OWNER,
    github_repo=GITHUB_REPO,
    github_branch=GITHUB_BRANCH,
    target=target,
    env=cdk.Environment(
        account=os.getenv("CDK_DEFAULT_ACCOUNT"),
        region=os.getenv("CDK_DEFAULT_REGION"),
    ),
)

app.synth()