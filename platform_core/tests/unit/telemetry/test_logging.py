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


def test_invalid_severity_is_rejected():
    bind_context(trace_id="abc-123", app_id="snack-recommender", team="platform-eng", environment="staging")
    stream = io.StringIO()
    logger = PlatformLogger(stream=stream)

    with pytest.raises(ValueError):
        logger.log("oops", "something happened")

    assert stream.getvalue() == ""


@pytest.mark.parametrize(
    "method_name,expected_severity",
    [("debug", "debug"), ("warn", "warn"), ("error", "error"), ("critical", "critical")],
)
def test_remaining_convenience_methods_map_to_their_severity(method_name, expected_severity):
    bind_context(trace_id="abc-123", app_id="snack-recommender", team="platform-eng", environment="staging")
    stream = io.StringIO()
    logger = PlatformLogger(stream=stream)

    getattr(logger, method_name)("something happened")

    record = json.loads(stream.getvalue().strip())
    assert record["severity"] == expected_severity


def test_custom_fields_extend_the_schema():
    bind_context(trace_id="abc-123", app_id="snack-recommender", team="platform-eng", environment="staging")
    stream = io.StringIO()
    logger = PlatformLogger(stream=stream)

    logger.info("payment processed", order_id="ord_789")

    record = json.loads(stream.getvalue().strip())
    assert record["order_id"] == "ord_789"
    assert record["trace_id"] == "abc-123"
