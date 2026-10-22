---
date: 2026-10-22
sequence: 02
commit: 09f0931
---

# instrument_call, and a second stdout field-name collision with OTel's own span JSON

Implemented #338: `platform_core.telemetry.spans.instrument_call(resource, operation, call,
logger=None)` -- observes a call to a storage dependency (not propagation; a storage system has
nothing to hand a trace_id to) as one structured entry with `resource`/`operation`/`duration_ms`/
`outcome`, logged via whichever adapter is given (defaults to a fresh `ServiceAdapter`).

**A second, different stdout field-name collision with OTel's own span JSON.** #249's work
already established that span-export lines and our own structured-log lines legitimately share
stdout now, and that tests need to filter by the `severity` key (unique to our schema) rather
than assume every line is one of ours. Writing this story's own field also named `resource`
collided with that same pattern in a new way: OTel's span JSON itself has a top-level `resource`
key (the span's Resource attributes), so a naive `"resource" in record` filter matched both our
log entry and the span dump. Fixed the test to filter by `severity` instead, consistent with the
existing pattern -- but worth flagging that any future field name chosen for a telemetry record
should be checked against OTel's own span JSON shape first, not just against this codebase's own
schema, now that both live on the same stream.

Integration scenario runs against snack-recommender's real SQLAlchemy connection (SQLite
in-memory, via the app's existing `aws_secrets.get_database_url()` local fallback -- no AWS
credentials needed, same fallback `test_telemetry.py` already relies on), proving a real measured
duration, not a stub.
