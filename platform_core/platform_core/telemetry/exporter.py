import os

from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter, SimpleSpanProcessor

VALID_EXPORTERS = ("log", "otlp")


def build_span_processor():
    exporter_kind = os.environ.get("OTEL_EXPORTER", "log")

    if exporter_kind == "log":
        return SimpleSpanProcessor(ConsoleSpanExporter())

    if exporter_kind == "otlp":
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

        endpoint = os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"]
        return BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint))

    raise ValueError(
        f"Invalid OTEL_EXPORTER {exporter_kind!r}; must be one of: {', '.join(VALID_EXPORTERS)}"
    )
