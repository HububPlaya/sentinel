from dataclasses import dataclass


@dataclass(frozen=True)
class IamConfig:
    """Naming for IAM resources created for the web app's compute instances."""
    role_name: str = "webapp-eb-ec2-role"
    instance_profile_name: str = "webapp-eb-ec2-instance-profile"