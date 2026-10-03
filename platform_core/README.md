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

Every log line includes five required fields: `trace_id`, `app_id`, `team`, `environment`,
`severity`. The library enforces this -- a log call missing any of them, with no active context
to supply it, raises `MissingRequiredFieldError` instead of silently emitting an incomplete
record.

### 1. Bind context once per request/task

```python
from platform_core.telemetry.context import bind_context

bind_context(
    trace_id="...",       # usually a generated UUID, or propagated from an inbound header
    app_id="snack-recommender",
    team="platform-eng",
    environment="staging",
)
```

In a Flask app, do this in a `before_request` hook so every request gets a fresh context
automatically. `clear_context()` resets it; `get_context()` reads the current binding (mostly
useful for tests).

### 2. Log

```python
from platform_core.telemetry.logging import PlatformLogger

logger = PlatformLogger()
logger.info("payment processed")
logger.error("payment failed", order_id="ord_789")
```

Available methods: `.debug()`, `.info()`, `.warn()`, `.error()`, `.critical()` -- each maps to
one of the platform's fixed severities. An undefined severity raises `ValueError` before
anything is written. By default, output goes to `sys.stdout` (what Elastic Beanstalk/CloudWatch
actually captures) -- pass `stream=` to `PlatformLogger()` to redirect it (tests do this with a
`StringIO`).

Any field not in the required five that doesn't match an explicit argument passes through
unchanged, so the schema is extendable per call without any change here:

```python
logger.info("payment processed", order_id="ord_789", amount=42.50)
# -> {"trace_id": "...", "app_id": "...", "team": "...", "environment": "...",
#     "severity": "info", "message": "payment processed", "order_id": "ord_789", "amount": 42.5}
```

### 3. Propagate trace context through outbound HTTP calls

```python
from platform_core.telemetry.http import TracedSession

session = TracedSession()
session.get("https://downstream.example/api/thing")
```

`TracedSession` is a drop-in `requests.Session` subclass -- use it exactly like `requests.Session`
for any outbound call. If there's an active context (see step 1), it attaches the current
trace_id as an `X-Trace-Id` header automatically; with no active context, it behaves like a plain
`Session` and doesn't force a header.

Not yet covered: propagation into a Lambda invocation (no Lambda app exists on the platform yet
to build or test one against).

## Required environment/config per consuming app

A consuming app needs to supply, per its own config mechanism:

- `APP_ID` -- the app's own identifier
- `TEAM` -- owning team (currently just a config value; no real team registry exists yet to
  pull this from)
- `ENVIRONMENT` -- which environment this instance is running in (`dev`, `staging`, `prod`, etc.)

`trace_id` is per-request and should be generated (or propagated from an inbound trace header)
at the point context is bound, not set as a static config value.

## Testing

```
pip install -r requirements-dev.txt
pytest
```

Coverage is enforced at a minimum of 90% (`--cov-fail-under=90` in `pyproject.toml`); a plain
`pytest` run fails below that automatically.
