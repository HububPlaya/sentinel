import io
import json

import pytest

from platform_core.telemetry.context import bind_context, clear_context
from platform_core.telemetry.logging import MissingRequiredFieldError, PlatformLogger


def test_raises_when_no_context_and_no_explicit_fields():
    clear_context()
    logger = PlatformLogger()

    with pytest.raises(MissingRequiredFieldError):
        logger.info("payment processed")


def test_auto_injects_trace_id_from_active_request_context():
    bind_context(trace_id="abc-123", app_id="snack-recommender", team="platform-eng", environment="staging")
    stream = io.StringIO()
    logger = PlatformLogger(stream=stream)

    logger.info("payment processed")

    record = json.loads(stream.getvalue().strip())
    assert record["trace_id"] == "abc-123"
