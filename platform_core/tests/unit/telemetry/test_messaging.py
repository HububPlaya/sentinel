from platform_core.telemetry.context import start_span
from platform_core.telemetry.messaging import extract_and_attach, inject


def test_active_spans_context_is_injected_into_a_plain_dict_carrier():
    carrier = {}

    with start_span("producer") as span:
        trace_id = format(span.get_span_context().trace_id, "032x")
        inject(carrier)

    assert "traceparent" in carrier
    assert trace_id in carrier["traceparent"]


def test_extracting_a_carrier_continues_the_same_trace():
    carrier = {}
    with start_span("producer") as span:
        producer_trace_id = format(span.get_span_context().trace_id, "032x")
        inject(carrier)

    with extract_and_attach(carrier) as consumer_span:
        consumer_trace_id = format(consumer_span.get_span_context().trace_id, "032x")

    assert consumer_trace_id == producer_trace_id


def test_empty_carrier_starts_an_independent_trace():
    with extract_and_attach({}) as span:
        trace_id = format(span.get_span_context().trace_id, "032x")

    assert trace_id is not None
    assert len(trace_id) == 32
