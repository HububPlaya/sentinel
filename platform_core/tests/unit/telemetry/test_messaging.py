from platform_core.telemetry.context import start_span
from platform_core.telemetry.messaging import inject


def test_active_spans_context_is_injected_into_a_plain_dict_carrier():
    carrier = {}

    with start_span("producer") as span:
        trace_id = format(span.get_span_context().trace_id, "032x")
        inject(carrier)

    assert "traceparent" in carrier
    assert trace_id in carrier["traceparent"]
