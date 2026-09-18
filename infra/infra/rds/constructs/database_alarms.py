from aws_cdk import aws_cloudwatch as cloudwatch
from aws_cdk import aws_rds as rds
from constructs import Construct


class DatabaseAlarms(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        database: rds.IDatabaseInstance,
        allocated_storage_gb: int,
    ) -> None:
        super().__init__(scope, construct_id)

        self.high_cpu_alarm = cloudwatch.Alarm(
            self, "HighCpuAlarm",
            metric=database.metric_cpu_utilization(),
            threshold=80,
            evaluation_periods=3,
            datapoints_to_alarm=3,
            alarm_description="CPU utilization above 80% for 15 minutes",
        )

        low_storage_threshold_bytes = allocated_storage_gb * 1024 * 1024 * 1024 * 0.2
        self.low_storage_alarm = cloudwatch.Alarm(
            self, "LowStorageAlarm",
            metric=database.metric_free_storage_space(),
            threshold=low_storage_threshold_bytes,
            comparison_operator=cloudwatch.ComparisonOperator.LESS_THAN_THRESHOLD,
            evaluation_periods=1,
            alarm_description="Free storage below 20% of allocated storage",
        )