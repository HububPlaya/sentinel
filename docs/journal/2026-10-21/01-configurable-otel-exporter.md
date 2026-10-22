---
date: 2026-10-21
sequence: 01
commit: 1545c03
---

# Configurable OTel exporter: spans had nowhere to go until now

Implemented #331: `platform_core.telemetry.exporter.build_span_processor()`, defaulting to a
real console exporter, swappable to OTLP via `OTEL_EXPORTER`/`OTEL_EXPORTER_OTLP_ENDPOINT`.

**Spans were silently going nowhere before this.** `context.configure()` (from #329) built a
`TracerProvider` but never attached a span processor/exporter to it -- every span created so far
was real, correctly correlated, and completely unobservable. Wiring `build_span_processor()`'s
result into `configure()` is what actually makes any of this visible.

**`ConsoleSpanExporter`'s `out` default is bound at import time, not per call.** Its `out`
parameter defaults to `sys.stdout`, but as a literal object reference captured once when the
`opentelemetry.sdk.trace.export` module is first imported -- not re-read on each instantiation.
Neither `capsys` nor `capfd` reliably see output through that stale reference in a test. Fixed by
passing `out=sys.stdout` explicitly in our own code at call time, which is also the more correct
production behavior (honors a later stdout reassignment, e.g. under gunicorn), not just a test
workaround.

Chose `SimpleSpanProcessor` for the console exporter (synchronous, deterministic -- fine for
printing) and `BatchSpanProcessor` for OTLP (batched, since it's a real network call per export
and shouldn't block the request path on every single span).
