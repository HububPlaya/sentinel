---
date: 2026-10-22
sequence: 01
commit: 8f78bc6
---

# Library/service telemetry adapters, and a real stdout collision #331 introduced

Implemented #249: `LibraryAdapter` (self-contained, no background thread, doesn't touch the
shared `context` module's global state) and `ServiceAdapter` (a pure alias for `PlatformLogger`,
formalizing the name per the story's own implementation notes rather than rebuilding anything).
Both produce the identical schema via a shared `logging.build_record()`, extracted out of
`PlatformLogger.log()` as a pure refactor first.

**The background-thread requirement surfaced a real gap in #331's exporter.** `BatchSpanProcessor`
always starts a worker thread, regardless of which exporter it wraps -- OTLP export configured on
a library-mode adapter would have violated #249's own "no background thread" AC. Added
`build_span_processor(force_synchronous=True)`, which always returns a `SimpleSpanProcessor`
instead, so library-mode gets OTLP export without ever spawning a thread.

**A real production bug, found only by running a real app.** Wiring `snack-recommender` to
actually use `ServiceAdapter` (previously it only imported `PlatformLogger` directly) and running
its full suite was the first time any request has actually exercised #331's exporter wiring
end-to-end, rather than a unit test in isolation. `ConsoleSpanExporter`'s default `to_json()` is
pretty-printed (`indent=4`, multi-line) -- interleaved on the same stdout stream as this
codebase's one-JSON-object-per-line structured logs, every span corrupted line-based parsing of
real output. This isn't just a test artifact: CloudWatch (or anything reading stdout as one
log-record-per-line) would see the exact same interleaved mess in production. Fixed with a
compact single-line formatter on the exporter. `snack-recommender`'s own tests were then updated
to filter stdout lines by the `severity` key rather than assume every line is one of our own log
records, since span-export lines and structured-log lines now both legitimately share that
stream.

Lambda-mode adapter stays deferred, same as the story said -- no Lambda app exists yet to build
or test one against.
