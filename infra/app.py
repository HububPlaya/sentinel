#!/usr/bin/env python3
import os

import aws_cdk as cdk
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_iam as iam

from infra.elastic_beanstalk.application_stack import ApplicationStack
from infra.elastic_beanstalk.network_stack import NetworkStack
from infra.elastic_beanstalk.environment_stack import EnvironmentStack
from infra.elastic_beanstalk.config import ENVIRONMENTS
from infra.rds.database_stack import DatabaseStack
from infra.rds.config import DATABASE_CONFIGS

app = cdk.App()

APP_NAME = "snack-recommender"

env = cdk.Environment(
    account=os.getenv("CDK_DEFAULT_ACCOUNT"),
    region=os.getenv("CDK_DEFAULT_REGION"),
)

application_stack = ApplicationStack(app, "SnackRecommenderApplication", app_name=APP_NAME, env=env)

target_env = app.node.try_get_context("env") or "dev"

if target_env not in ENVIRONMENTS:
    raise ValueError(f"Unknown environment '{target_env}'. Valid options: {list(ENVIRONMENTS)}")

env_config = ENVIRONMENTS[target_env]

network_stack = NetworkStack(
    app, f"SnackRecommenderNetwork-{target_env}",
    app_name=APP_NAME, env_name=target_env, env=env,
)

database_stack = DatabaseStack(
    app, f"SnackRecommenderDatabase-{target_env}",
    app_name=APP_NAME, env_name=target_env, config=DATABASE_CONFIGS[target_env], env=env,
)

app_environment_variables = {
    "DB_HOST": database_stack.database.instance.db_instance_endpoint_address,
    "DB_PORT": database_stack.database.instance.db_instance_endpoint_port,
    "DB_NAME": database_stack.database.database_name,
    "DB_SECRET_ARN": database_stack.database.instance.secret.secret_arn,
    "DB_SECRET_REGION": env.region,
}
if database_stack.read_replica:
    app_environment_variables["DB_READ_HOST"] = database_stack.read_replica.instance.db_instance_endpoint_address
    
environment_stack = EnvironmentStack(
    app, f"SnackRecommenderInfra-{target_env}",
    app_name=APP_NAME, env_config=env_config,
    security_group=network_stack.security_group,
    app_environment_variables=app_environment_variables,
    env=env,
)

environment_stack.add_dependency(application_stack)

ec2.CfnSecurityGroupIngress(
    environment_stack, "AllowDbIngressFromEb",
    group_id=database_stack.database.security_group.security_group_id,
    source_security_group_id=network_stack.security_group.security_group_id,
    ip_protocol="tcp",
    from_port=database_stack.database.PORT,
    to_port=database_stack.database.PORT,
    description="Postgres access from EB app instances",
)

if database_stack.read_replica:
    ec2.CfnSecurityGroupIngress(
        environment_stack, "AllowDbReadReplicaIngressFromEb",
        group_id=database_stack.read_replica.security_group.security_group_id,
        source_security_group_id=network_stack.security_group.security_group_id,
        ip_protocol="tcp",
        from_port=database_stack.read_replica.PORT,
        to_port=database_stack.read_replica.PORT,
        description="Postgres access from EB app instances (reads)",
    )

environment_stack.instance_role.role.add_to_policy(
    iam.PolicyStatement(
        actions=["secretsmanager:GetSecretValue"],
        resources=[database_stack.database.instance.secret.secret_arn],
    )
)

app.synth()