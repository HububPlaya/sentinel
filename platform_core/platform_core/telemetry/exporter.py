import os

from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor

VALID_EXPORTERS = ("log", "otlp")


def build_span_processor():
    exporter_kind = os.environ.get("OTEL_EXPORTER", "log")

    if exporter_kind == "log":
        return SimpleSpanProcessor(ConsoleSpanExporter())

    raise ValueError(
        f"Invalid OTEL_EXPORTER {exporter_kind!r}; must be one of: {', '.join(VALID_EXPORTERS)}"
    )
