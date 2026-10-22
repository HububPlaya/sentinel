import os
import sys

from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter, SimpleSpanProcessor

VALID_EXPORTERS = ("log", "otlp")


def build_span_processor(*, force_synchronous: bool = False):
    exporter_kind = os.environ.get("OTEL_EXPORTER", "log")

    if exporter_kind == "log":
        # out=sys.stdout passed explicitly: ConsoleSpanExporter's own default
        # for `out` is bound once at module-import time, not re-read per call,
        # so it would otherwise silently ignore any later stdout reassignment
        # (ours in production, or a test's capture fixture).
        #
        # formatter: ReadableSpan.to_json() defaults to indent=4 (pretty,
        # multi-line) -- interleaved with this codebase's own one-JSON-
        # object-per-line structured logs, that corrupts line-based parsing
        # of real stdout (CloudWatch, or any test reading captured output).
        # Compact single-line JSON matches the existing log convention.
        return SimpleSpanProcessor(
            ConsoleSpanExporter(out=sys.stdout, formatter=lambda span: span.to_json(indent=None) + "\n")
        )

    if exporter_kind == "otlp":
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

        endpoint = os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"]
        exporter = OTLPSpanExporter(endpoint=endpoint)
        # force_synchronous=True exists for library-mode: a library with no
        # runtime of its own can't spawn a background thread the way a
        # long-lived service can, so it needs the otlp exporter wrapped in a
        # SimpleSpanProcessor (synchronous, no worker thread) instead of
        # BatchSpanProcessor (which always starts one).
        return SimpleSpanProcessor(exporter) if force_synchronous else BatchSpanProcessor(exporter)

    raise ValueError(
        f"Invalid OTEL_EXPORTER {exporter_kind!r}; must be one of: {', '.join(VALID_EXPORTERS)}"
    )
