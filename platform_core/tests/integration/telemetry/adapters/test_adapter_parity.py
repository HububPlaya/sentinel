import io
import json

from platform_core.telemetry.adapters.library import LibraryAdapter
from platform_core.telemetry.adapters.service import ServiceAdapter
from platform_core.telemetry.context import configure, reset, start_span


def test_library_and_service_mode_output_the_identical_schema():
    reset()
    configure(app_id="snack-recommender", team="platform-eng", environment="staging")
    service_stream = io.StringIO()
    service_adapter = ServiceAdapter(stream=service_stream)

    with start_span("service event"):
        service_adapter.log("info", "event emitted", order_id="ord_789")

    library_stream = io.StringIO()
    library_adapter = LibraryAdapter(
        app_id="snack-sdk", team="platform-eng", environment="dev", stream=library_stream
    )

    with library_adapter.start_span("library event"):
        library_adapter.log("info", "event emitted", order_id="ord_789")

    service_record = json.loads(service_stream.getvalue().strip())
    library_record = json.loads(library_stream.getvalue().strip())

    assert service_record.keys() == library_record.keys()
