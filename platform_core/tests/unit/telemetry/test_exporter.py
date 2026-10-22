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


def test_force_synchronous_never_returns_a_batch_processor_even_for_otlp(monkeypatch):
    monkeypatch.setenv("OTEL_EXPORTER", "otlp")
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://collector:4317")

    processor = build_span_processor(force_synchronous=True)

    assert isinstance(processor, SimpleSpanProcessor)
    assert isinstance(processor.span_exporter, OTLPSpanExporter)
