from dataclasses import dataclass


@dataclass(frozen=True)
class TargetRef:
    resource_type: str
    source_path: str
    application_name: str
    environment_name: str


def _snack_recommender_target(env_name: str) -> TargetRef:
    return TargetRef(
        resource_type="elastic_beanstalk",
        source_path="test-apps/snack-recommender",
        application_name="snack-recommender",
        environment_name=f"snack-recommender-{env_name}",
    )


TARGETS: dict[tuple[str, str], TargetRef] = {
    ("snack-recommender", "dev"): _snack_recommender_target("dev"),
    ("snack-recommender", "test"): _snack_recommender_target("test"),
    ("snack-recommender", "stage"): _snack_recommender_target("stage"),
    ("snack-recommender", "prod"): _snack_recommender_target("prod"),
}