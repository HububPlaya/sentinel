from platform_core.telemetry.context import configure, reset, start_span


def test_real_span_exported_via_the_log_exporter_appears_on_stdout(monkeypatch, capsys):
    monkeypatch.delenv("OTEL_EXPORTER", raising=False)
    reset()

    configure(app_id="snack-recommender", team="platform-eng", environment="dev")
    with start_span("request"):
        pass

    captured = capsys.readouterr()
    assert "request" in captured.out
