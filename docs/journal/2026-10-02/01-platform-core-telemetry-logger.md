---
date: 2026-10-02
sequence: 01
commit: 725969a
---

# New platform_core shared package, built test-first

First shared library in the repo, not tied to any one app. Matches `infra/`/`pipeline/`'s
project/tests layout (project-named inner package, sibling `tests/` dir), but needed its own
`pyproject.toml` since, unlike those two, this package is meant to be *imported* by consumer
apps rather than run directly.

Scope: `platform_core.telemetry` -- a structured logger enforcing five required fields
(trace_id, app_id, team, environment, severity) on every log line, with context bound once per
request via `contextvars` so application code doesn't thread those fields through every call by
hand. Schema is extendable: unrecognized keyword args pass through as custom fields untouched.

Built one test-driven cycle at a time: write the scenario's test, confirm it fails for the right
reason (missing module/attribute, not a typo), write the minimum code to pass it, confirm green,
commit. Each cycle is its own commit on `feat/telemetry-logging-schema` -- the commit log itself
is the more detailed record of how this was built than this entry is.

Then wired into `snack-recommender`'s request lifecycle (`before_request` binds context,
`/health` and a generic error handler both log through it) as the first real consumer, proving
the library against an actual app rather than only its own unit tests.

90% test coverage enforced via `pytest-cov`, wired into `pyproject.toml` so a plain `pytest` run
fails below it automatically -- not just a number someone has to remember to check.
