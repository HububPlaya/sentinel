#!/usr/bin/env python3
import os

import aws_cdk as cdk

from infra.elastic_beanstalk.infra_stack import InfraStack
from infra.elastic_beanstalk.config import ENVIRONMENTS

app = cdk.App()

target_env = app.node.try_get_context("env") or "dev"

if target_env not in ENVIRONMENTS:
    raise ValueError(f"Unknown environment '{target_env}'. Valid options: {list(ENVIRONMENTS)}")

env_config = ENVIRONMENTS[target_env]

InfraStack(
    app, f"WebappInfra-{target_env}",
    app_name="webapp",
    env_config=env_config,
    env=cdk.Environment(
        account=os.getenv("CDK_DEFAULT_ACCOUNT"),
        region=os.getenv("CDK_DEFAULT_REGION"),
    ),
)

app.synth()