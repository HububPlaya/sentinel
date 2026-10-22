import io
import json

from platform_core.telemetry.adapters.service import ServiceAdapter
from platform_core.telemetry.context import configure, reset, start_span
from platform_core.telemetry.logging import PlatformLogger


def test_service_adapter_matches_platform_logger_existing_behavior():
    reset()
    configure(app_id="snack-recommender", team="platform-eng", environment="staging")
    adapter_stream = io.StringIO()
    logger_stream = io.StringIO()
    adapter = ServiceAdapter(stream=adapter_stream)
    logger = PlatformLogger(stream=logger_stream)

    with start_span("request"):
        adapter.log("info", "payment processed", order_id="ord_789")
        logger.log("info", "payment processed", order_id="ord_789")

    adapter_record = json.loads(adapter_stream.getvalue().strip())
    logger_record = json.loads(logger_stream.getvalue().strip())
    assert adapter_record == logger_record
