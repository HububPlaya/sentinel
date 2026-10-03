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
