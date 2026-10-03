import json

from app import create_app
from app.config import Config


class TestConfig(Config):
    TESTING = True


def test_real_request_emits_structured_log_with_required_fields(capsys):
    app = create_app(TestConfig)
    client = app.test_client()

    client.get("/health")

    captured = capsys.readouterr()
    log_lines = [line for line in captured.out.strip().splitlines() if line]
    assert log_lines, "expected at least one structured log line for the request"

    record = json.loads(log_lines[-1])
    for field in ("trace_id", "app_id", "team", "environment", "severity"):
        assert field in record
    assert record["app_id"] == "snack-recommender"


def test_one_trace_id_persists_across_multiple_log_calls_in_one_request(capsys):
    app = create_app(TestConfig)
    client = app.test_client()

    client.get("/health")

    captured = capsys.readouterr()
    log_lines = [line for line in captured.out.strip().splitlines() if line]
    assert len(log_lines) >= 2, "expected at least two log lines for one /health request"

    records = [json.loads(line) for line in log_lines]
    trace_ids = {record["trace_id"] for record in records}
    assert len(trace_ids) == 1, f"expected one shared trace_id, got {trace_ids}"


def test_context_does_not_leak_across_sequential_requests(capsys):
    app = create_app(TestConfig)
    client = app.test_client()

    client.get("/health")
    request_a_trace_ids = {
        json.loads(line)["trace_id"] for line in capsys.readouterr().out.strip().splitlines() if line
    }

    client.get("/health")
    request_b_trace_ids = {
        json.loads(line)["trace_id"] for line in capsys.readouterr().out.strip().splitlines() if line
    }

    assert request_a_trace_ids.isdisjoint(request_b_trace_ids)
