import io
import json

import pytest

from platform_core.telemetry.context import configure, reset, start_span
from platform_core.telemetry.logging import MissingRequiredFieldError, PlatformLogger


def test_raises_when_not_configured_and_no_active_span():
    reset()
    logger = PlatformLogger()

    with pytest.raises(MissingRequiredFieldError):
        logger.info("payment processed")


def test_log_inside_an_active_span_is_correlated_to_it():
    configure(app_id="snack-recommender", team="platform-eng", environment="staging")
    stream = io.StringIO()
    logger = PlatformLogger(stream=stream)

    with start_span("request") as span:
        trace_id = format(span.get_span_context().trace_id, "032x")
        logger.info("payment processed")

    record = json.loads(stream.getvalue().strip())
    assert record["trace_id"] == trace_id
    assert record["app_id"] == "snack-recommender"
    assert record["team"] == "platform-eng"
    assert record["environment"] == "staging"


def test_invalid_severity_is_rejected():
    configure(app_id="snack-recommender", team="platform-eng", environment="staging")
    stream = io.StringIO()
    logger = PlatformLogger(stream=stream)

    with start_span("request"):
        with pytest.raises(ValueError):
            logger.log("oops", "something happened")

    assert stream.getvalue() == ""


@pytest.mark.parametrize(
    "method_name,expected_severity",
    [("debug", "debug"), ("warn", "warn"), ("error", "error"), ("critical", "critical")],
)
def test_remaining_convenience_methods_map_to_their_severity(method_name, expected_severity):
    configure(app_id="snack-recommender", team="platform-eng", environment="staging")
    stream = io.StringIO()
    logger = PlatformLogger(stream=stream)

    with start_span("request"):
        getattr(logger, method_name)("something happened")

    record = json.loads(stream.getvalue().strip())
    assert record["severity"] == expected_severity


def test_custom_fields_extend_the_schema():
    configure(app_id="snack-recommender", team="platform-eng", environment="staging")
    stream = io.StringIO()
    logger = PlatformLogger(stream=stream)

    with start_span("request") as span:
        trace_id = format(span.get_span_context().trace_id, "032x")
        logger.info("payment processed", order_id="ord_789")

    record = json.loads(stream.getvalue().strip())
    assert record["order_id"] == "ord_789"
    assert record["trace_id"] == trace_id
