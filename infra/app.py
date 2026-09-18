#!/usr/bin/env python3
import os

import aws_cdk as cdk

from infra.elastic_beanstalk.application_stack import ApplicationStack
from infra.elastic_beanstalk.environment_stack import EnvironmentStack
from infra.elastic_beanstalk.config import ENVIRONMENTS

app = cdk.App()

APP_NAME = "snack-recommender"

env = cdk.Environment(
    account=os.getenv("CDK_DEFAULT_ACCOUNT"),
    region=os.getenv("CDK_DEFAULT_REGION"),
)

ApplicationStack(app, "SnackRecommenderApplication", app_name=APP_NAME, env=env)

target_env = app.node.try_get_context("env") or "dev"

if target_env not in ENVIRONMENTS:
    raise ValueError(f"Unknown environment '{target_env}'. Valid options: {list(ENVIRONMENTS)}")

env_config = ENVIRONMENTS[target_env]

EnvironmentStack(
    app, f"SnackRecommenderInfra-{target_env}",
    app_name=APP_NAME,
    env_config=env_config,
    env=env,
)

app.synth()