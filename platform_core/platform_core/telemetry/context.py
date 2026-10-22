import contextvars
from contextlib import contextmanager

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider

from .exporter import build_span_processor
from .resource import build_resource

_resource_attributes: dict = {}
_tracer = TracerProvider().get_tracer("platform_core")
_origin_var: "contextvars.ContextVar[str]" = contextvars.ContextVar(
    "platform_core_telemetry_origin", default="internal"
)


def configure(*, app_id: str, team: str, environment: str) -> None:
    global _resource_attributes, _tracer
    _resource_attributes = {"app_id": app_id, "team": team, "environment": environment}
    resource = build_resource(app_id=app_id, team=team, environment=environment)
    provider = TracerProvider(resource=resource)
    provider.add_span_processor(build_span_processor())
    _tracer = provider.get_tracer("platform_core")


def current_resource_attributes() -> dict:
    return dict(_resource_attributes)


@contextmanager
def start_span(name: str, *, origin: str = "internal"):
    token = _origin_var.set(origin)
    try:
        with _tracer.start_as_current_span(name) as span:
            yield span
    finally:
        _origin_var.reset(token)


def current_origin() -> str:
    return _origin_var.get()


def reference_id(trace_id: str) -> str:
    """Short, deterministic, customer-facing derivation of a real trace_id -- safe to
    put in an error response, unlike the full internal trace_id."""
    return trace_id[:8]


def reset() -> None:
    global _resource_attributes, _tracer
    _resource_attributes = {}
    _tracer = TracerProvider().get_tracer("platform_core")


def current_trace_id() -> "str | None":
    span_context = trace.get_current_span().get_span_context()
    if not span_context.is_valid:
        return None
    return format(span_context.trace_id, "032x")
