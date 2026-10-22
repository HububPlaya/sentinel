from enum import Enum

from opentelemetry._logs import SeverityNumber


class Severity(str, Enum):
    """The platform's fixed severity set. No app may introduce its own values --
    an undefined severity must never reach the log pipeline."""

    DEBUG = "debug"
    INFO = "info"
    WARN = "warn"
    ERROR = "error"
    CRITICAL = "critical"

    @classmethod
    def coerce(cls, value):
        if isinstance(value, cls):
            return value
        try:
            return cls(value)
        except ValueError:
            valid = ", ".join(s.value for s in cls)
            raise ValueError(f"Invalid severity {value!r}; must be one of: {valid}") from None

    def to_otel(self) -> SeverityNumber:
        return _OTEL_SEVERITY_NUMBER[self]


_OTEL_SEVERITY_NUMBER = {
    Severity.DEBUG: SeverityNumber.DEBUG,
    Severity.INFO: SeverityNumber.INFO,
    Severity.WARN: SeverityNumber.WARN,
    Severity.ERROR: SeverityNumber.ERROR,
    Severity.CRITICAL: SeverityNumber.FATAL,
}
