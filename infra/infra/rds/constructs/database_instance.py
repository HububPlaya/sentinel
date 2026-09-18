from aws_cdk import Duration, RemovalPolicy
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_kms as kms
from aws_cdk import aws_rds as rds
from constructs import Construct

from ..config import DatabaseConfig


class DatabaseInstance(Construct):
    PORT = 5432

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        vpc: ec2.IVpc,
        app_name: str,
        env_name: str,
        config: DatabaseConfig,
        encryption_key: kms.IKey,
    ) -> None:
        super().__init__(scope, construct_id)

        self.database_name = app_name.replace("-", "_")

        self.security_group = ec2.SecurityGroup(
            self, "SecurityGroup",
            vpc=vpc,
            description=f"RDS instance for {app_name}-{env_name}",
            allow_all_outbound=False,
        )

        self.instance = rds.DatabaseInstance(
            self, "Instance",
            engine=rds.DatabaseInstanceEngine.postgres(version=rds.PostgresEngineVersion.VER_16_4),
            instance_type=ec2.InstanceType(config.instance_class),
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC),
            security_groups=[self.security_group],
            credentials=rds.Credentials.from_generated_secret(
                f"{app_name}_{env_name}_db_user".replace("-", "_"),
                encryption_key=encryption_key,
            ),
            database_name=self.database_name,
            allocated_storage=config.allocated_storage_gb,
            storage_encrypted=True,
            storage_encryption_key=encryption_key,
            multi_az=config.multi_az,
            deletion_protection=config.deletion_protection,
            backup_retention=Duration.days(config.backup_retention_days),
            removal_policy=RemovalPolicy.RETAIN if config.deletion_protection else RemovalPolicy.DESTROY,
            publicly_accessible=False,
            cloudwatch_logs_exports=["postgresql"],
        )

    def allow_ingress_from(self, peer: ec2.IPeer, description: str) -> None:
        self.security_group.add_ingress_rule(peer=peer, connection=ec2.Port.tcp(self.PORT), description=description)