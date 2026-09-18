from aws_cdk import Stack
from aws_cdk import aws_ec2 as ec2
from constructs import Construct

from infra.elastic_beanstalk.constructs import ElasticBeanstalkSecurityGroup


class NetworkStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, *, app_name: str, env_name: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.vpc = ec2.Vpc.from_lookup(self, "Vpc", is_default=True)

        self.eb_security_group = ElasticBeanstalkSecurityGroup(
            self, "SecurityGroup", vpc=self.vpc, app_name=app_name, env_name=env_name,
        )
        self.security_group = self.eb_security_group.security_group