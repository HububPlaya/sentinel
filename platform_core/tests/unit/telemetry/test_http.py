from platform_core.telemetry.context import bind_context, clear_context
from platform_core.telemetry.http import TracedSession


def test_outbound_call_attaches_the_active_trace_header(requests_mock):
    bind_context(trace_id="t-1", app_id="snack-recommender", team="platform-eng", environment="staging")
    requests_mock.get("http://downstream.example/ping", json={"ok": True})

    session = TracedSession()
    session.get("http://downstream.example/ping")

    sent_headers = requests_mock.request_history[0].headers
    assert sent_headers["X-Trace-Id"] == "t-1"
