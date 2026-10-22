from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

_propagator = TraceContextTextMapPropagator()


def inject(carrier: dict) -> None:
    _propagator.inject(carrier)
