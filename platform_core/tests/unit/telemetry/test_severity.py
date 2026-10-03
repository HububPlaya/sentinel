import pytest
from opentelemetry._logs import SeverityNumber

from platform_core.telemetry.severity import Severity


@pytest.mark.parametrize(
    "severity,expected",
    [
        (Severity.DEBUG, SeverityNumber.DEBUG),
        (Severity.INFO, SeverityNumber.INFO),
        (Severity.WARN, SeverityNumber.WARN),
        (Severity.ERROR, SeverityNumber.ERROR),
        (Severity.CRITICAL, SeverityNumber.FATAL),
    ],
)
def test_to_otel_maps_every_severity_to_a_severity_number(severity, expected):
    assert severity.to_otel() == expected
