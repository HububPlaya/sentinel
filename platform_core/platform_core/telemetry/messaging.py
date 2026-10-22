from contextlib import contextmanager

from opentelemetry import context as otel_context
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

from .context import start_span

_propagator = TraceContextTextMapPropagator()


def inject(carrier: dict) -> None:
    _propagator.inject(carrier)


@contextmanager
def extract_and_attach(carrier: dict, name: str = "consumer"):
    extracted_context = _propagator.extract(carrier)
    token = otel_context.attach(extracted_context)
    try:
        with start_span(name) as span:
            yield span
    finally:
        otel_context.detach(token)
