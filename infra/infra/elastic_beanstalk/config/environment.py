from dataclasses import dataclass, field

from .scaling import AutoScalingConfig
from .instance import InstanceConfig
from .iam import IamConfig

ENVIRONMENT_NAMES: list[str] = ["dev", "test", "stage", "prod"]


@dataclass(frozen=True)
class EnvConfig:
    """Full configuration for a single deployment environment (dev/test/stage/prod)."""
    env_name: str
    scaling: AutoScalingConfig
    instance: InstanceConfig = field(default_factory=InstanceConfig)
    iam: IamConfig = field(default_factory=IamConfig)
    # us-east-1e in this account doesn't support t3 instance types (confirmed by a
    # real deploy failure). AWS randomizes each account's AZ name-to-physical
    # mapping, so this is account-specific. Kept as real per-env data since a
    # future environment with a different instance_type could need different AZs.
    availability_zones: list[str] = field(default_factory=lambda: ["us-east-1a", "us-east-1b"])


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

assert set(ENVIRONMENTS.keys()) == set(ENVIRONMENT_NAMES), (
    f"ENVIRONMENTS keys {set(ENVIRONMENTS.keys())} don't match ENVIRONMENT_NAMES {set(ENVIRONMENT_NAMES)}"
)