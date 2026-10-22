import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import requests

from platform_core.telemetry.context import start_span
from platform_core.telemetry.http import instrument


class _CapturingHandler(BaseHTTPRequestHandler):
    captured_headers = None

    def do_GET(self):
        _CapturingHandler.captured_headers = dict(self.headers)
        self.send_response(200)
        self.end_headers()

    def log_message(self, *args):
        pass


def test_real_outbound_call_carries_a_decodable_traceparent_header():
    instrument()
    server = HTTPServer(("127.0.0.1", 0), _CapturingHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    try:
        with start_span("request") as span:
            trace_id = format(span.get_span_context().trace_id, "032x")
            requests.get(f"http://127.0.0.1:{server.server_port}/")
    finally:
        server.shutdown()
        thread.join()

    traceparent = _CapturingHandler.captured_headers["traceparent"]
    # W3C format: version-trace_id-parent_id-flags
    _, decoded_trace_id, _, _ = traceparent.split("-")
    assert decoded_trace_id == trace_id
