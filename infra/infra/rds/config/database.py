from dataclasses import dataclass


@dataclass(frozen=True)
class DatabaseConfig:
    instance_class: str = "t3.micro"
    allocated_storage_gb: int = 20
    multi_az: bool = False
    deletion_protection: bool = False
    backup_retention_days: int = 1
    has_read_replica: bool = True
    read_replica_instance_class: str = "t3.micro"


DATABASE_CONFIGS: dict[str, DatabaseConfig] = {
    "dev": DatabaseConfig(),
    "test": DatabaseConfig(),
    "stage": DatabaseConfig(backup_retention_days=7),
    "prod": DatabaseConfig(
        instance_class="t3.small",
        multi_az=True,
        deletion_protection=True,
        backup_retention_days=7,
        read_replica_instance_class="t3.small",
    ),
}