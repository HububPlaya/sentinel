from platform_core.telemetry.context import configure, current_resource_attributes, current_trace_id, start_span


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
