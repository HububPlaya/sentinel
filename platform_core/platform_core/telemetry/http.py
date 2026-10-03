import requests

from .context import get_context

TRACE_HEADER = "X-Trace-Id"


class TracedSession(requests.Session):
    """A requests.Session that attaches the active context's trace_id as an outbound
    header automatically, so callers don't attach it by hand at every call site."""

    def request(self, method, url, **kwargs):
        context = get_context()
        if context and context.get("trace_id"):
            headers = kwargs.pop("headers", {}) or {}
            headers.setdefault(TRACE_HEADER, context["trace_id"])
            kwargs["headers"] = headers
        return super().request(method, url, **kwargs)
