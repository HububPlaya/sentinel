from aws_cdk import aws_elasticbeanstalk as eb
from constructs import Construct


class ElasticBeanstalkApplication(Construct):
    def __init__(self, scope: Construct, construct_id: str, *, app_name: str) -> None:
        super().__init__(scope, construct_id)
        self.application = eb.CfnApplication(self, "Application", application_name=app_name)