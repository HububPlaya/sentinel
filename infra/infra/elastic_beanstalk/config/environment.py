from dataclasses import dataclass, field

from .scaling import AutoScalingConfig
from .instance import InstanceConfig
from .iam import IamConfig


@dataclass(frozen=True)
class EnvConfig:
    """Full configuration for a single deployment environment (dev/test/stage/prod)."""
    env_name: str
    scaling: AutoScalingConfig
    instance: InstanceConfig = field(default_factory=InstanceConfig)
    iam: IamConfig = field(default_factory=IamConfig)


ENVIRONMENTS: dict[str, EnvConfig] = {
    "dev": EnvConfig(
        env_name="dev",
        scaling=AutoScalingConfig(min_instances=1, max_instances=1),
    ),
    "test": EnvConfig(
        env_name="test",
        scaling=AutoScalingConfig(min_instances=1, max_instances=2),
    ),
    "stage": EnvConfig(
        env_name="stage",
        scaling=AutoScalingConfig(min_instances=2, max_instances=4),
    ),
    "prod": EnvConfig(
        env_name="prod",
        scaling=AutoScalingConfig(min_instances=2, max_instances=6),
        instance=InstanceConfig(instance_type="t3.small"),
    ),
}