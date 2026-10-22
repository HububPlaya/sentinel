import json
import sys
from typing import IO

from opentelemetry.sdk.trace import TracerProvider

from ..context import current_trace_id
from ..exporter import build_span_processor
from ..logging import build_record
from ..resource import build_resource


class LibraryAdapter:
    """Telemetry adapter for a library with no runtime of its own -- self-contained,
    does not touch platform_core.telemetry.context's shared global state, and never
    spawns a background thread (force_synchronous=True on its span processor). Flush
    is the host application's own responsibility; there is no background thread to
    flush on its own."""

    def __init__(self, *, app_id: str, team: str, environment: str, stream: "IO[str] | None" = None):
        self._stream = stream if stream is not None else sys.stdout
        self._resource_attributes = {"app_id": app_id, "team": team, "environment": environment}

        resource = build_resource(app_id=app_id, team=team, environment=environment)
        provider = TracerProvider(resource=resource)
        provider.add_span_processor(build_span_processor(force_synchronous=True))
        self._tracer = provider.get_tracer("platform_core")

    def start_span(self, name: str):
        return self._tracer.start_as_current_span(name)

    def log(self, severity, message: str, **fields) -> None:
        record = build_record(severity, message, self._resource_attributes, current_trace_id(), fields)
        self._stream.write(json.dumps(record) + "\n")
