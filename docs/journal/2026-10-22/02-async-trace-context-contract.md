---
date: 2026-10-22
sequence: 02
commit: 28fae2a
---

# Async trace-context contract: adopted OTel's propagator directly

Implemented #337: carrying trace context across an async hop (a queue message, not an HTTP
call) that has no header to attach a `traceparent` to.

The story's own implementation notes said to evaluate OTel's `TraceContextTextMapPropagator`
against a plain dict carrier before hand-rolling anything -- verified it directly rather than
assuming: `propagator.inject({})` writes a real `traceparent` key encoding the active span's
trace_id into any dict-like carrier, and `propagator.extract(carrier)` + `context.attach()`
correctly makes a child span share that same trace_id, with an empty/missing carrier falling
back to a fresh independent trace rather than erroring. All three of the story's AC scenarios
were already covered by the library itself.

So `platform_core.telemetry.messaging` ended up as a ~15-line wrapper (`inject()`,
`extract_and_attach()` mirroring `start_span()`'s context-manager shape) rather than a
hand-written inject/extract contract -- same build-vs-adopt pattern #330 applied when it adopted
`opentelemetry-instrumentation-requests` instead of writing a `requests.Session` subclass.

Deliberately transport-agnostic: the carrier is just a plain dict. Wrapping it into a real
SQS `MessageAttributes` shape, an SNS attribute map, or Kafka headers is each transport's own
concern -- out of scope here, and blocked anyway on real async infrastructure (#340) not existing
yet.
