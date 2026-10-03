from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider

from .resource import build_resource

_resource_attributes: dict = {}
_tracer = TracerProvider().get_tracer("platform_core")


def configure(*, app_id: str, team: str, environment: str) -> None:
    global _resource_attributes, _tracer
    _resource_attributes = {"app_id": app_id, "team": team, "environment": environment}
    resource = build_resource(app_id=app_id, team=team, environment=environment)
    _tracer = TracerProvider(resource=resource).get_tracer("platform_core")


def current_resource_attributes() -> dict:
    return dict(_resource_attributes)


def start_span(name: str):
    return _tracer.start_as_current_span(name)


def current_trace_id() -> "str | None":
    span_context = trace.get_current_span().get_span_context()
    if not span_context.is_valid:
        return None
    return format(span_context.trace_id, "032x")
