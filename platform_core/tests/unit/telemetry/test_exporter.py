from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor

from platform_core.telemetry.exporter import build_span_processor


def test_default_configuration_uses_the_log_exporter(monkeypatch):
    monkeypatch.delenv("OTEL_EXPORTER", raising=False)

    processor = build_span_processor()

    assert isinstance(processor, SimpleSpanProcessor)
    assert isinstance(processor.span_exporter, ConsoleSpanExporter)
