import json

from app import create_app
from app.config import Config


class TestConfig(Config):
    TESTING = True


def _structured_logs(text):
    """Stdout now also carries real OTel span-export lines (since #331) --
    same stream, different schema. Our own structured logs are the only ones
    with a top-level `severity` key; a span dump has `context`/`kind`/etc.
    instead, so filter rather than assume every stdout line is one of ours."""
    records = (json.loads(line) for line in text.strip().splitlines() if line)
    return [record for record in records if "severity" in record]


def test_real_request_emits_structured_log_with_required_fields(capsys):
    app = create_app(TestConfig)
    client = app.test_client()

    client.get("/health")

    records = _structured_logs(capsys.readouterr().out)
    assert records, "expected at least one structured log line for the request"

    record = records[-1]
    for field in ("trace_id", "app_id", "team", "environment", "severity"):
        assert field in record
    assert record["app_id"] == "snack-recommender"


def test_one_trace_id_persists_across_multiple_log_calls_in_one_request(capsys):
    app = create_app(TestConfig)
    client = app.test_client()

    client.get("/health")

    records = _structured_logs(capsys.readouterr().out)
    assert len(records) >= 2, "expected at least two log lines for one /health request"

    trace_ids = {record["trace_id"] for record in records}
    assert len(trace_ids) == 1, f"expected one shared trace_id, got {trace_ids}"


def test_context_does_not_leak_across_sequential_requests(capsys):
    app = create_app(TestConfig)
    client = app.test_client()

    client.get("/health")
    request_a_trace_ids = {record["trace_id"] for record in _structured_logs(capsys.readouterr().out)}

    client.get("/health")
    request_b_trace_ids = {record["trace_id"] for record in _structured_logs(capsys.readouterr().out)}

    assert request_a_trace_ids.isdisjoint(request_b_trace_ids)


def test_error_paths_still_produce_a_structured_log(capsys):
    app = create_app(TestConfig)
    # TESTING=True defaults PROPAGATE_EXCEPTIONS on, which bypasses error handlers for
    # debugging convenience. Production doesn't propagate, so this test opts back out
    # to exercise the real error-handling path.
    app.config["PROPAGATE_EXCEPTIONS"] = False

    @app.get("/__boom")
    def boom():
        raise RuntimeError("boom")

    client = app.test_client()
    client.get("/__boom")

    records = _structured_logs(capsys.readouterr().out)
    assert any(record["severity"] == "error" for record in records), (
        f"expected a structured error-severity log, got: {records}"
    )


def test_error_response_exposes_reference_id_not_the_full_trace_id(capsys):
    app = create_app(TestConfig)
    app.config["PROPAGATE_EXCEPTIONS"] = False

    @app.get("/__boom2")
    def boom():
        raise RuntimeError("boom")

    client = app.test_client()
    response = client.get("/__boom2")

    records = _structured_logs(capsys.readouterr().out)
    real_trace_id = next(record["trace_id"] for record in records if record["severity"] == "error")

    body = response.get_json()
    assert "reference_id" in body
    assert body["reference_id"] == real_trace_id[:8]
    assert real_trace_id not in json.dumps(body)


def test_logs_go_to_stdout_not_stderr(capsys):
    app = create_app(TestConfig)
    client = app.test_client()

    client.get("/health")

    captured = capsys.readouterr()
    assert captured.out.strip(), "expected log output on stdout"
    assert captured.err == "", f"expected nothing on stderr, got: {captured.err!r}"
