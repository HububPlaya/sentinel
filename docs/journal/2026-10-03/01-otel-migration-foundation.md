---
date: 2026-10-03
sequence: 01
commit: 668ace0
---

# Migrating the telemetry foundation to real OpenTelemetry

Replaced `platform_core.telemetry`'s hand-rolled `contextvars` trace scheme with the real
OpenTelemetry SDK (#329). Three decisions worth recording:

**Resource vs. span context are genuinely different lifetimes.** The old `bind_context()`
conflated `app_id`/`team`/`environment` (static per-service identity) with `trace_id` (dynamic,
per-request) into one dict, re-set on every request even though three of its four fields never
change for the life of the process. OTel has a real distinction for this -- `Resource` (set once
at startup) vs. span context (created per request) -- and splitting along that line directly
fixed a latent bug in the old design: `snack-recommender` was re-declaring its own `app_id`/
`team`/`environment` on every single request for no reason.

**Skipped the OTel Logs SDK for now.** The original plan was to move `PlatformLogger` onto
OTel's `LoggerProvider`/`Logger.emit()`. In practice that module (`opentelemetry.sdk._logs`) is
still underscore-prefixed and its API shape doesn't match the public docs for the installed
version (1.45.0) -- `LogRecord` isn't importable from there the way examples suggest, and wiring
a real exporter means building `LogRecordProcessor`/`LogExporter` machinery that's actually
#331's job, not this story's. Kept `PlatformLogger` writing JSON directly to a stream, but now
sourcing `trace_id` from the real active OTel span and `severity_number` from a new
`Severity.to_otel()` mapping. The full Logs SDK adoption can happen in #331 once exporter
configuration is actually in scope.

**`SpanContext.is_valid`, not truthiness of a formatted id.** An inactive OTel span's trace_id is
literally `0`, which formats to a 32-character string of zeroes -- a non-empty, truthy string.
Checking `current_trace_id() is None` via plain truthiness would have silently treated "no active
span" as "trace_id present." Used `SpanContext.is_valid` explicitly instead.

Also discovered while updating `snack-recommender`: the old `before_request` hook was rebuilding
`app_id`/`team`/`environment` on every request, which is exactly the kind of bug the
Resource/span-context split above exists to prevent. `configure()` now runs once in `create_app()`;
`before_request`/`teardown_request` only open and close the per-request span.
