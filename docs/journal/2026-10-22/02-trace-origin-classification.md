---
date: 2026-10-22
sequence: 02
commit: 0a8cdcf
---

# Trace origin (#339): a parallel contextvar, not an OTel-native concept

Implemented #339: `start_span(name, origin="internal")` and a `current_origin()` readback,
plus `reference_id(trace_id)` -- a short, deterministic, customer-facing derivation of the real
trace_id.

**Origin needed its own contextvar, separate from the span itself.** Unlike `trace_id`/`span_id`,
there's no OTel-native concept of "origin" to piggyback on -- it's purely this platform's own
classification. Rather than trying to stash it as a span attribute and read it back off the live
span object (which the OTel API doesn't make straightforward), it's a plain `contextvars.ContextVar`
scoped to `start_span`'s duration, the same pattern the pre-OTel-migration `bind_context` used for
`trace_id` itself. `start_span` became a `@contextmanager`-wrapped generator to set/reset it
around the real OTel span's own context manager.

**Origin is global, not per-adapter, on purpose.** Both `ServiceAdapter` and `LibraryAdapter`
read `current_origin()` the same way they already share `current_trace_id()` -- origin describes
*this request/task*, not which adapter instance happens to be logging it, so there's no reason
for `LibraryAdapter`'s otherwise-self-contained design (see #249) to maintain its own copy.

**Reference id is a pure derivation, not a second generated id** -- `trace_id[:8]`, deterministic,
so the same trace always produces the same reference without a lookup table anywhere. Wired into
`snack-recommender`'s error handler in place of exposing the full `trace_id` directly.
