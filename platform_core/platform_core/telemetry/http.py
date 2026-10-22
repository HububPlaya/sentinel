from opentelemetry.instrumentation.requests import RequestsInstrumentor


def instrument() -> None:
    RequestsInstrumentor().instrument()
