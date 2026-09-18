from aws_cdk import RemovalPolicy
from aws_cdk import aws_kms as kms
from constructs import Construct


class DatabaseEncryptionKey(Construct):
    def __init__(
        self, scope: Construct, construct_id: str, *, app_name: str, env_name: str, retain: bool,
    ) -> None:
        super().__init__(scope, construct_id)

        self.key = kms.Key(
            self, "Key",
            alias=f"{app_name}-{env_name}-rds",
            description=f"Encrypts RDS storage and credentials for {app_name}-{env_name}",
            enable_key_rotation=True,
            removal_policy=RemovalPolicy.RETAIN if retain else RemovalPolicy.DESTROY,
        )