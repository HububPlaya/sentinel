from platform_core.telemetry.context import (
    configure,
    current_origin,
    current_resource_attributes,
    current_trace_id,
    reference_id,
    start_span,
)


def test_resource_attributes_are_set_once_from_app_id_team_environment():
    configure(app_id="snack-recommender", team="platform-eng", environment="dev")

    attrs = current_resource_attributes()

    assert attrs["app_id"] == "snack-recommender"
    assert attrs["team"] == "platform-eng"
    assert attrs["environment"] == "dev"


def test_started_span_gets_a_real_otel_trace_id():
    assert current_trace_id() is None

    with start_span("request"):
        trace_id = current_trace_id()

    assert trace_id is not None
    assert len(trace_id) == 32
    int(trace_id, 16)


def test_origin_defaults_to_internal_when_not_specified():
    with start_span("job"):
        assert current_origin() == "internal"


def test_origin_can_be_explicitly_set_to_customer():
    with start_span("request", origin="customer"):
        assert current_origin() == "customer"


def test_reference_id_is_a_short_deterministic_derivation_of_the_trace_id():
    trace_id = "62287cb32cf20a29764599d4c382f1e4"

    ref = reference_id(trace_id)

    assert ref == reference_id(trace_id)  # deterministic -- same input, same output
    assert len(ref) == 8
    assert trace_id.startswith(ref)
