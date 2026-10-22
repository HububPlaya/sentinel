from unittest.mock import patch

import requests
import requests.adapters

from platform_core.telemetry.context import start_span
from platform_core.telemetry.http import instrument


def _capture_sent_headers():
    captured = {}

    def fake_send(self, request, **kwargs):
        captured.update(request.headers)
        response = requests.Response()
        response.status_code = 200
        response.request = request
        return response

    return captured, fake_send


def test_outbound_call_attaches_a_real_traceparent_header():
    instrument()
    captured, fake_send = _capture_sent_headers()

    with patch.object(requests.adapters.HTTPAdapter, "send", fake_send):
        with start_span("request") as span:
            trace_id = format(span.get_span_context().trace_id, "032x")
            requests.get("http://example.com")

    assert "traceparent" in captured
    assert trace_id in captured["traceparent"]
