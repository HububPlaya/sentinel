from dataclasses import dataclass


@dataclass(frozen=True)
class AutoScalingConfig:
    min_instances: int
    max_instances: int