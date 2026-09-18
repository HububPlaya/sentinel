from aws_cdk import Stack
from constructs import Construct

from infra.elastic_beanstalk.constructs import ElasticBeanstalkApplication


class ApplicationStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, *, app_name: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        self.application = ElasticBeanstalkApplication(self, "Application", app_name=app_name)