from dataclasses import dataclass


@dataclass(frozen=True)
class IamConfig:
    role_name_suffix: str = "eb-ec2-role"
    instance_profile_name_suffix: str = "eb-ec2-instance-profile"