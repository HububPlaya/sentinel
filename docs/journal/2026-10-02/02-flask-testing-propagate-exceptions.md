---
date: 2026-10-02
sequence: 02
commit: 7de2901
---

# TESTING=True silently bypasses registered error handlers

Writing the "unhandled exceptions still produce a structured log" test for snack-recommender's
telemetry wiring, a route raising `RuntimeError` propagated straight out of the Flask test
client instead of reaching the registered `app.errorhandler(Exception)` handler at all.

Cause: `TESTING=True` defaults `PROPAGATE_EXCEPTIONS` on, which makes Flask re-raise unhandled
exceptions for debugger convenience instead of routing them through registered handlers for
generic `Exception`. Production doesn't set `TESTING`, so `PROPAGATE_EXCEPTIONS` is off there by
default and the handler runs normally -- meaning the test, as first written, wasn't actually
exercising production behavior at all.

Fix: explicitly set `app.config["PROPAGATE_EXCEPTIONS"] = False` in the test's app config, so the
test opts back into the real error-handling path rather than Flask's test-mode shortcut. Worth
remembering for any future test of error-handling behavior in this app -- the default `TESTING`
config actively works against testing that specific thing.
