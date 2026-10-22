import io
import json

import pytest

from platform_core.telemetry.adapters.service import ServiceAdapter
from platform_core.telemetry.context import configure, reset, start_span
from platform_core.telemetry.spans import instrument_call


def test_successful_call_emits_structured_entry_with_resource_duration_and_success_outcome():
    reset()
    configure(app_id="snack-recommender", team="platform-eng", environment="staging")
    stream = io.StringIO()
    logger = ServiceAdapter(stream=stream)

    with start_span("request"):
        result = instrument_call(
            resource="rds:snack-recommender-db",
            operation="select_snacks",
            call=lambda: "snacks",
            logger=logger,
        )

    assert result == "snacks"
    record = json.loads(stream.getvalue().strip())
    assert record["resource"] == "rds:snack-recommender-db"
    assert record["operation"] == "select_snacks"
    assert record["outcome"] == "success"
    assert record["duration_ms"] >= 0
