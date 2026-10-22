import pytest
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter, SimpleSpanProcessor

from platform_core.telemetry.exporter import build_span_processor


def test_default_configuration_uses_the_log_exporter(monkeypatch):
    monkeypatch.delenv("OTEL_EXPORTER", raising=False)

    processor = build_span_processor()

    assert isinstance(processor, SimpleSpanProcessor)
    assert isinstance(processor.span_exporter, ConsoleSpanExporter)


def test_otlp_exporter_is_selected_and_configured_from_env(monkeypatch):
    monkeypatch.setenv("OTEL_EXPORTER", "otlp")
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://collector:4317")

    processor = build_span_processor()

    assert isinstance(processor, BatchSpanProcessor)
    assert isinstance(processor.span_exporter, OTLPSpanExporter)
    assert processor.span_exporter._endpoint == "collector:4317"


def test_invalid_exporter_value_fails_loudly(monkeypatch):
    monkeypatch.setenv("OTEL_EXPORTER", "nonsense")

    with pytest.raises(ValueError, match="nonsense"):
        build_span_processor()


def test_default_log_exporter_emits_compact_single_line_json(monkeypatch):
    import io
    import json

    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider

    monkeypatch.delenv("OTEL_EXPORTER", raising=False)
    stream = io.StringIO()

    processor = build_span_processor()
    processor.span_exporter.out = stream
    provider = TracerProvider(resource=Resource.create({}))
    provider.add_span_processor(processor)
    tracer = provider.get_tracer("test")

    with tracer.start_as_current_span("request"):
        pass

    lines = [line for line in stream.getvalue().splitlines() if line]
    assert len(lines) == 1, f"expected one compact line per span, got: {lines}"
    json.loads(lines[0])  # must be valid, complete JSON on its own


def test_force_synchronous_never_returns_a_batch_processor_even_for_otlp(monkeypatch):
    monkeypatch.setenv("OTEL_EXPORTER", "otlp")
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://collector:4317")

    processor = build_span_processor(force_synchronous=True)

    assert isinstance(processor, SimpleSpanProcessor)
    assert isinstance(processor.span_exporter, OTLPSpanExporter)
