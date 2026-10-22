# platform_core

Shared platform capabilities for every app onboarded to the platform. Currently covers
structured telemetry logging; more capabilities (tracing, tagging, identity helpers, etc.)
land here as their own stories.

## Install

From a consuming app, add an editable local dependency (adjust the relative path to wherever
`platform_core` actually sits relative to the consumer):

```
-e ../../platform_core
```

## `platform_core.telemetry`

Built on the real OpenTelemetry SDK (`opentelemetry-api`/`opentelemetry-sdk`), not a hand-rolled
context/id scheme. Every log line includes five required fields: `trace_id`, `app_id`, `team`,
`environment`, `severity`. The library enforces this -- a log call missing any of them, with no
active span/resource to supply it, raises `MissingRequiredFieldError` instead of silently
emitting an incomplete record.

`app_id`/`team`/`environment` are static per-service identity -- they describe *this process*,
not any one request, so they're OTel **Resource** attributes configured once at startup.
`trace_id`/`span_id` are the dynamic, per-request part, and come from a real OTel span.

### 1. Configure once per process

```python
from platform_core.telemetry.context import configure

configure(app_id="snack-recommender", team="platform-eng", environment="staging")
```

Do this once, at app startup -- not per request. In a Flask app, this belongs in `create_app()`,
not in a `before_request` hook.

### 2. Start a span per request/task

```python
from platform_core.telemetry.context import start_span

with start_span("request"):
    ...  # anything logged in here is correlated to this span's trace_id
```

In a Flask app, open the span in `before_request` and close it in `teardown_request` (passing
through any exception info), since Flask has no single hook that spans the whole request --
see `test-apps/snack-recommender/app/__init__.py` for the real pattern. `context.reset()` clears
the configured resource and tracer (mostly useful for tests, same role the old `clear_context()`
played).

### 3. Log -- pick the adapter that matches how your code runs

A long-lived service and a library with no runtime of its own need mechanically different ways
to emit telemetry (a library can't run its own background exporter thread). Both produce the
exact same structured schema underneath.

**Service-mode** -- a long-lived process (a Flask app, a worker), context bound per
request/task via `configure()`/`start_span()` above:

```python
from platform_core.telemetry.adapters.service import ServiceAdapter

logger = ServiceAdapter()
logger.info("payment processed")
logger.error("payment failed", order_id="ord_789")
```

This is exactly `PlatformLogger` (importable either way) -- `ServiceAdapter` is just the name
this story gives it, formalizing what every consuming app already does, not new behavior.

**Library-mode** -- embedded inside someone else's application, with no runtime or background
thread of its own. Self-contained: it does not touch `context.configure()`'s shared global
state (so it can't clobber whatever the host application itself has configured), and never
spawns a background thread even if OTLP export is configured, since `BatchSpanProcessor` always
starts one:

```python
from platform_core.telemetry.adapters.library import LibraryAdapter

adapter = LibraryAdapter(app_id="snack-sdk", team="platform-eng", environment="dev")

with adapter.start_span("operation"):
    adapter.log("info", "event emitted")
```

Flushing is the host application's own responsibility -- there's no background thread for this
library to flush on its own.

Available severity methods on `ServiceAdapter`/`PlatformLogger`: `.debug()`, `.info()`, `.warn()`,
`.error()`, `.critical()` -- each maps to one of the platform's fixed severities (`LibraryAdapter`
exposes the same severities through `.log(severity, message, **fields)` directly). An undefined
severity raises `ValueError` before anything is written. By default, output goes to `sys.stdout`
(what Elastic Beanstalk/CloudWatch actually captures) -- pass `stream=` to redirect it (tests do
this with a `StringIO`).

Any field not in the required five that doesn't match an explicit argument passes through
unchanged, so the schema is extendable per call without any change here:

```python
logger.info("payment processed", order_id="ord_789", amount=42.50)
# -> {"trace_id": "...", "app_id": "...", "team": "...", "environment": "...",
#     "severity": "info", "message": "payment processed", "order_id": "ord_789", "amount": 42.5}
```

### 4. Where do spans actually go?

Nothing extra to configure if you have no observability backend yet: `configure()` wires up a
real exporter automatically, defaulting to `OTEL_EXPORTER=log` -- every span prints as compact,
single-line structured JSON to stdout (not the OTel SDK's own pretty-printed default, which would
otherwise corrupt line-based parsing of a stream also carrying your own log records), same place
your logs already go, no new infrastructure to run.

If a team already has an OTel-compatible backend (Dynatrace, Datadog, Grafana Tempo, Jaeger --
anything that accepts OTLP), point at it instead:

```
OTEL_EXPORTER=otlp
OTEL_EXPORTER_OTLP_ENDPOINT=http://collector:4317
```

No display/stitching logic is built by this library either way -- the "nothing yet" case gets
readable stdout output, and the "already have a backend" case gets real OTLP spans that backend
already knows how to render. An unrecognized `OTEL_EXPORTER` value raises immediately at startup
rather than silently falling back to one or the other.

### 5. Propagate traces across outbound HTTP calls

```python
from platform_core.telemetry.http import instrument

instrument()  # once at startup, alongside configure()
```

Turns on `opentelemetry-instrumentation-requests`, which attaches the active span's context as a
real W3C `traceparent` header to every outbound call made via `requests`, so a trace started in
one service is readable by any OTel-aware consumer it calls into -- not just our own code. No
header is forced when there's no active span. Adopted directly rather than hand-writing a
`requests.Session` subclass -- it already covers exactly this behavior; see the journal entry for
how that was verified before committing to it.

### 6. Observe a call to a storage dependency

```python
from platform_core.telemetry.spans import instrument_call

rows = instrument_call(
    resource="rds:snack-recommender-db",
    operation="select_snacks",
    call=lambda: Snack.query.all(),
)
```

A storage system (a database, a bucket) doesn't participate in trace propagation -- there's
nothing to hand a `trace_id` to or get one back from. `instrument_call` isn't propagation, it's
observability of the call itself: one structured entry with `resource`, `operation`,
`duration_ms`, and `outcome` (`success`/`error`), logged as one more hop in the active trace. The
wrapped call's own exception still propagates -- this only observes it, never swallows it.

Deliberately records only the resource's own identifier, not who owns it. A caller doesn't
reliably know who owns a shared resource it merely calls, and asking every call site to declare
it drifts the moment ownership changes -- resolving *who owns this* is a lookup against this
platform's resource tagging/inventory at query/display time (see #248), not a field stamped here.

By default, logs via a fresh `ServiceAdapter()` (so it works with no setup against anything
already using the shared `context` module); pass `logger=` to use a specific adapter instance
instead (e.g. a `LibraryAdapter`).

### 7. Classify trace origin, and give customers a safe reference id

Not every trace starts from a real customer request -- a cron job or a deploy step has no
customer anywhere in its ancestry. `start_span` takes an `origin`, defaulting to `"internal"`
(the safer default: don't assume customer-facing unless explicitly declared):

```python
from platform_core.telemetry.context import start_span

with start_span("request", origin="customer"):
    ...  # every log emitted in here carries origin="customer"
```

Every structured log record carries the active span's `origin`. In a Flask app, pass
`origin="customer"` in `before_request` -- a real inbound HTTP request always starts from a
customer, unlike an internal/scheduled job.

When you need to hand a customer something traceable back to a real trace (an error response,
a support ticket), don't expose the full internal `trace_id` -- derive a short reference instead:

```python
from platform_core.telemetry.context import current_trace_id, reference_id

ref = reference_id(current_trace_id())  # first 8 hex chars, deterministic
```

See `test-apps/snack-recommender/app/__init__.py`'s error handler for the real pattern --
`reference_id` in the response body, the full `trace_id` never exposed there.

### 8. Propagate traces across an async hop (no HTTP header to attach to)

A queue (SQS, SNS, Kafka) has no header -- the trace context has to travel as a plain
attribute on the message instead. This is transport-agnostic: the carrier is just a dict;
wrapping it into a real SQS/SNS/Kafka attribute format is each transport's own concern, out
of scope here.

Producer side:

```python
from platform_core.telemetry.messaging import inject

carrier = {}
inject(carrier)  # carrier now has a traceparent key -- attach it to your message's attributes
```

Consumer side:

```python
from platform_core.telemetry.messaging import extract_and_attach

with extract_and_attach(carrier) as span:
    ...  # this span shares the producer's trace_id; an empty/missing carrier just starts a fresh one
```

Built directly on OTel's own `TraceContextTextMapPropagator` -- verified against a plain dict
carrier before adopting it rather than hand-writing inject/extract, same build-vs-adopt check
applied to the HTTP instrumentation above.

## Required environment/config per consuming app

A consuming app needs to supply, per its own config mechanism:

- `APP_ID` -- the app's own identifier
- `TEAM` -- owning team (currently just a config value; no real team registry exists yet to
  pull this from)
- `ENVIRONMENT` -- which environment this instance is running in (`dev`, `staging`, `prod`, etc.)
- `OTEL_EXPORTER` -- optional, defaults to `log`; set to `otlp` plus `OTEL_EXPORTER_OTLP_ENDPOINT`
  to export to a real backend instead

`trace_id`/`span_id` are generated by the OTel SDK itself when `start_span()` is called -- there's
nothing to generate or pass in by hand.

## Testing

```
pip install -r requirements-dev.txt
pytest
```

Coverage is enforced at a minimum of 90% (`--cov-fail-under=90` in `pyproject.toml`); a plain
`pytest` run fails below that automatically.
