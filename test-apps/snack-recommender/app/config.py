import os

from . import aws_secrets


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")
    SQLALCHEMY_DATABASE_URI = aws_secrets.get_database_url()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DATABASE_READ_URL = aws_secrets.get_database_read_url()

    # Telemetry context (platform_core.telemetry) -- team ownership isn't pulled from a
    # real registry yet since that platform capability doesn't exist; hardcoded here until it does.
    APP_ID = "snack-recommender"
    TEAM = os.environ.get("TEAM", "platform-eng")
    ENVIRONMENT = os.environ.get("ENVIRONMENT", "dev")