import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from platform_core.telemetry.context import bind_context, clear_context
from platform_core.telemetry.http import TracedSession


class _CapturingHandler(BaseHTTPRequestHandler):
    captured_headers = None

    def do_GET(self):
        _CapturingHandler.captured_headers = dict(self.headers)
        self.send_response(200)
        self.end_headers()

    def log_message(self, format, *args):
        pass  # keep test output quiet


@pytest.fixture
def local_server():
    server = HTTPServer(("127.0.0.1", 0), _CapturingHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield server
    server.shutdown()
    thread.join()


def test_real_outbound_call_to_local_server_carries_the_trace_header(local_server):
    bind_context(trace_id="t-real-1", app_id="snack-recommender", team="platform-eng", environment="staging")
    port = local_server.server_address[1]

    session = TracedSession()
    response = session.get(f"http://127.0.0.1:{port}/ping")

    assert response.status_code == 200
    assert _CapturingHandler.captured_headers.get("X-Trace-Id") == "t-real-1"

    clear_context()
