"""Fetches configuration that only exists on AWS -- database credentials from
Secrets Manager, combined with the non-sensitive connection details EB sets as
plain environment variables. Isolated here so config.py stays a plain
declaration of what Flask needs, not where those values come from -- same
separation used throughout infra/ (config/ vs. the constructs that produce it).
"""
import json
import os
from functools import lru_cache

import boto3
from botocore.config import Config as BotoConfig


def is_running_on_aws() -> bool:
    return "DB_SECRET_ARN" in os.environ


def get_database_url() -> str:
    if not is_running_on_aws():
        return os.environ.get("DATABASE_URL", "sqlite:///snack_recommender.db")

    credentials = _fetch_secret(os.environ["DB_SECRET_ARN"])
    host = os.environ["DB_HOST"]
    port = os.environ.get("DB_PORT", "5432")
    database = os.environ["DB_NAME"]

    return f"postgresql://{credentials['username']}:{credentials['password']}@{host}:{port}/{database}"


def get_database_read_url() -> str | None:
    if not is_running_on_aws():
        return None

    read_host = os.environ.get("DB_READ_HOST")
    if not read_host:
        return None

    credentials = _fetch_secret(os.environ["DB_SECRET_ARN"])
    port = os.environ.get("DB_PORT", "5432")
    database = os.environ["DB_NAME"]

    return f"postgresql://{credentials['username']}:{credentials['password']}@{read_host}:{port}/{database}"


@lru_cache
def _fetch_secret(secret_arn: str) -> dict:
    client = boto3.client(
        "secretsmanager",
        region_name=os.environ["DB_SECRET_REGION"],
        config=BotoConfig(retries={"max_attempts": 5, "mode": "standard"}),
    )
    response = client.get_secret_value(SecretId=secret_arn)
    return json.loads(response["SecretString"])