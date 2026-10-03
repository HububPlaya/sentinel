import json
import sys
from typing import IO

from .context import get_context
from .severity import Severity

REQUIRED_FIELDS = ("trace_id", "app_id", "team", "environment", "severity")


class MissingRequiredFieldError(RuntimeError):
    """Raised when a log would be emitted missing one of the platform's required fields,
    with no active request context to supply it and no explicit value given either."""


class PlatformLogger:
    def __init__(self, stream: "IO[str] | None" = None):
        self._stream = stream if stream is not None else sys.stdout

    def log(self, severity, message: str, **fields) -> None:
        severity = Severity.coerce(severity)

        context = get_context() or {}
        record = {
            "trace_id": fields.pop("trace_id", None) or context.get("trace_id"),
            "app_id": fields.pop("app_id", None) or context.get("app_id"),
            "team": fields.pop("team", None) or context.get("team"),
            "environment": fields.pop("environment", None) or context.get("environment"),
            "severity": severity.value,
        }

        missing = [field for field in REQUIRED_FIELDS if not record.get(field)]
        if missing:
            raise MissingRequiredFieldError(
                f"Cannot emit log: missing required field(s) {missing}."
            )

        record["message"] = message
        record.update(fields)
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
