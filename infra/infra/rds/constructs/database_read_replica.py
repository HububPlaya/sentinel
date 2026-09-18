from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_rds as rds
from constructs import Construct


class DatabaseReadReplica(Construct):
    PORT = 5432

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        vpc: ec2.IVpc,
        app_name: str,
        env_name: str,
        instance_class: str,
        source_database: rds.IDatabaseInstance,
    ) -> None:
        super().__init__(scope, construct_id)

        self.security_group = ec2.SecurityGroup(
            self, "SecurityGroup",
            vpc=vpc,
            description=f"RDS read replica for {app_name}-{env_name}",
            allow_all_outbound=False,
        )

        self.instance = rds.DatabaseInstanceReadReplica(
            self, "ReadReplica",
            source_database_instance=source_database,
            instance_type=ec2.InstanceType(instance_class),
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC),
            security_groups=[self.security_group],
            publicly_accessible=False,
        )

    def allow_ingress_from(self, peer: ec2.IPeer, description: str) -> None:
        self.security_group.add_ingress_rule(peer=peer, connection=ec2.Port.tcp(self.PORT), description=description)