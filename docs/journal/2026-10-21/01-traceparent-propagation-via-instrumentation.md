---
date: 2026-10-21
sequence: 01
commit: 5387d6a
---

# Traceparent propagation: adopted the instrumentation library, didn't hand-write it

Implemented #330: outbound HTTP calls now carry a real W3C `traceparent` header instead of the
bespoke `X-Trace-Id` header #247 had originally planned (never merged -- PR #328 was closed
unmerged once #329/#330 superseded it). Two things worth recording:

**Verified before adopting, not assumed.** The story's implementation notes said to evaluate
`opentelemetry-instrumentation-requests` first and adopt it directly if it covers both AC
scenarios. Tested both against a real local `http.server.HTTPServer`: with an active span, it
attaches a correctly-encoded `traceparent` header; with no active span, it attaches nothing and
the request still succeeds. Both match #330's AC exactly, so `platform_core.telemetry.http` ended
up as a three-line `instrument()` wrapper around the library, not a hand-written
`requests.Session` subclass. This directly reverses the header-format decision in
`docs/journal/2026-10-02/04-trace-propagation-http-header-choice.md` -- the reason given there (no
consumer for a standard header) no longer holds once interop with any OTel-aware backend is a
real goal.

**`requests-mock` silently hides the instrumentation's header injection.** First attempt at the
Unit-level test used `requests_mock.Mocker()`, matching the existing codebase pattern for Unit
tests. The injected `traceparent` header never showed up in `request_history` -- not an error,
just silently absent, which would have looked like "the library doesn't actually work" if not
checked against a real server first. The two mocking layers interact badly: `requests-mock`
replaces `requests.adapters.HTTPAdapter.send` globally in a way that bypasses whatever the
instrumentation's own wrapping of `Session.send` depends on to inject headers before the adapter
is reached. Switched to `unittest.mock.patch` directly on `HTTPAdapter.send`, which captures the
already-injected `PreparedRequest.headers` correctly -- confirmed by running the exact same
scenario against both mocking approaches side by side before picking one. Worth remembering for
any future test of OTel's auto-instrumentation libraries: don't assume `requests-mock` composes
cleanly with them.
