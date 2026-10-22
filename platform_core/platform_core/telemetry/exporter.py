import os
import sys

from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter, SimpleSpanProcessor

VALID_EXPORTERS = ("log", "otlp")


def build_span_processor():
    exporter_kind = os.environ.get("OTEL_EXPORTER", "log")

    if exporter_kind == "log":
        # out=sys.stdout passed explicitly: ConsoleSpanExporter's own default
        # for `out` is bound once at module-import time, not re-read per call,
        # so it would otherwise silently ignore any later stdout reassignment
        # (ours in production, or a test's capture fixture).
        return SimpleSpanProcessor(ConsoleSpanExporter(out=sys.stdout))

    if exporter_kind == "otlp":
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

        endpoint = os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"]
        return BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint))

    raise ValueError(
        f"Invalid OTEL_EXPORTER {exporter_kind!r}; must be one of: {', '.join(VALID_EXPORTERS)}"
    )
