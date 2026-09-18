from aws_cdk import Stack
from aws_cdk import aws_ec2 as ec2
from constructs import Construct

from .config import DatabaseConfig
from .constructs import DatabaseAlarms, DatabaseEncryptionKey, DatabaseInstance, DatabaseReadReplica


class DatabaseStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        app_name: str,
        env_name: str,
        config: DatabaseConfig,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.vpc = ec2.Vpc.from_lookup(self, "Vpc", is_default=True)

        self.encryption_key = DatabaseEncryptionKey(
            self, "EncryptionKey",
            app_name=app_name, env_name=env_name, retain=config.deletion_protection,
        )

        self.database = DatabaseInstance(
            self, "Database",
            vpc=self.vpc, app_name=app_name, env_name=env_name, config=config,
            encryption_key=self.encryption_key.key,
        )

        self.alarms = DatabaseAlarms(
            self, "Alarms",
            database=self.database.instance,
            allocated_storage_gb=config.allocated_storage_gb,
        )

        self.read_replica = None
        if config.has_read_replica:
            self.read_replica = DatabaseReadReplica(
                self, "ReadReplica",
                vpc=self.vpc, app_name=app_name, env_name=env_name,
                instance_class=config.read_replica_instance_class,
                source_database=self.database.instance,
            )