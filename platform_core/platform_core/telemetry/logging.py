import json
import sys
from typing import IO

from .context import current_resource_attributes, current_trace_id
from .severity import Severity

REQUIRED_FIELDS = ("trace_id", "app_id", "team", "environment", "severity")


class MissingRequiredFieldError(RuntimeError):
    """Raised when a log would be emitted missing one of the platform's required fields,
    with no active span/resource to supply it and no explicit value given either."""


def build_record(severity, message: str, resource_attrs: dict, trace_id: "str | None", fields: dict) -> dict:
    """Shared by every telemetry adapter (PlatformLogger/service-mode, library-mode) so
    they produce the identical schema despite sourcing trace_id/resource attrs differently."""
    severity = Severity.coerce(severity)

    record = {
        "trace_id": fields.pop("trace_id", None) or trace_id,
        "app_id": fields.pop("app_id", None) or resource_attrs.get("app_id"),
        "team": fields.pop("team", None) or resource_attrs.get("team"),
        "environment": fields.pop("environment", None) or resource_attrs.get("environment"),
        "severity": severity.value,
        "severity_number": severity.to_otel().value,
    }

    missing = [field for field in REQUIRED_FIELDS if not record.get(field)]
    if missing:
        raise MissingRequiredFieldError(f"Cannot emit log: missing required field(s) {missing}.")

    record["message"] = message
    record.update(fields)
    return record


class PlatformLogger:
    def __init__(self, stream: "IO[str] | None" = None):
        self._stream = stream if stream is not None else sys.stdout

    def log(self, severity, message: str, **fields) -> None:
        record = build_record(severity, message, current_resource_attributes(), current_trace_id(), fields)
        self._stream.write(json.dumps(record) + "\n")

    def debug(self, message: str, **fields) -> None:
        self.log("debug", message, **fields)

    def info(self, message: str, **fields) -> None:
        self.log("info", message, **fields)

    def warn(self, message: str, **fields) -> None:
        self.log("warn", message, **fields)

    def error(self, message: str, **fields) -> None:
        self.log("error", message, **fields)

    def critical(self, message: str, **fields) -> None:
        self.log("critical", message, **fields)
