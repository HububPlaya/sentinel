---
date: 2026-10-02
sequence: 04
commit: 0207ae7
---

# Trace propagation: a simple header now, real-server integration tests going forward

Built `platform_core.telemetry.http.TracedSession`, a `requests.Session` subclass that attaches
the active context's trace_id as an outbound header automatically. Two decisions worth recording:

**Header choice.** Used a plain `X-Trace-Id` header instead of the W3C `traceparent` standard
(version-traceid-parentid-flags format) the original story draft mentioned as an example. Nothing
on this platform parses `traceparent` yet, and implementing the real spec for a header nothing
reads back would be speculative complexity with no payoff right now. A custom header is simpler,
and swapping to `traceparent` later is a contained change inside one module if a real need for
interop with another tracing system shows up.

**Real-server integration testing.** The Integration/Component scenario needed a genuinely real
HTTP call, not another mock -- `requests-mock` (used for the Unit scenarios) fakes the transport
layer entirely, so it can't prove a header survives actual socket/HTTP framing. Spun up a real
`http.server.HTTPServer` on a background thread instead, and asserted the server itself received
the header. First use of this pattern in `platform_core`; new `tests/integration/` directory
alongside `tests/unit/`, same per-module structure. Worth reaching for the same pattern (a real
local server, not another mock) any time an Integration scenario is about whether something
survives a real network hop.

Lambda propagation is explicitly deferred -- no Lambda app exists on the platform yet to build or
test one against. Noted in the story and the README rather than silently left out.
