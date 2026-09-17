from dataclasses import dataclass


@dataclass(frozen=True)
class InstanceConfig:
    instance_type: str = "t3.micro"