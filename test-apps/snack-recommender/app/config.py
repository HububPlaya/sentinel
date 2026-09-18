import os

from . import aws_secrets


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")
    SQLALCHEMY_DATABASE_URI = aws_secrets.get_database_url()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DATABASE_READ_URL = aws_secrets.get_database_read_url()