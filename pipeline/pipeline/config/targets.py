from dataclasses import dataclass


@dataclass(frozen=True)
class TargetRef:
    resource_type: str      # "elastic_beanstalk", later "ecs_service", "kafka_topic", etc.
    source_path: str        # path in the repo to this app's source
    application_name: str   # the EB Application's name
    environment_name: str   # the EB Environment's name


TARGETS: dict[tuple[str, str], TargetRef] = {
    ("snack-recommender", "dev"): TargetRef(
        resource_type="elastic_beanstalk",
        source_path="test-apps/snack-recommender",
        application_name="snack-recommender",
        environment_name="snack-recommender-dev",
    ),
}