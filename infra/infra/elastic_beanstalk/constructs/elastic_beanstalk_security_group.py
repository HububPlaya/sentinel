from aws_cdk import aws_ec2 as ec2
from constructs import Construct


class ElasticBeanstalkSecurityGroup(Construct):
    def __init__(self, scope: Construct, construct_id: str, *, vpc: ec2.IVpc, app_name: str, env_name: str) -> None:
        super().__init__(scope, construct_id)

        self.security_group = ec2.SecurityGroup(
            self, "SecurityGroup",
            vpc=vpc,
            description=f"EC2 instances for {app_name}-{env_name}",
            allow_all_outbound=True,
        )