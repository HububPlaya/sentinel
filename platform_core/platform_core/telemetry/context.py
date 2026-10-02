import contextvars

# One context per logical request/task. Set once at the point a request/trigger enters the
# app, read implicitly by every log call made while it's active.
_context_var: "contextvars.ContextVar[dict | None]" = contextvars.ContextVar(
    "platform_core_telemetry_context", default=None
)


def bind_context(*, trace_id: str, app_id: str, team: str, environment: str) -> None:
    _context_var.set(
        {
            "trace_id": trace_id,
            "app_id": app_id,
            "team": team,
            "environment": environment,
        }
    )


def get_context() -> dict | None:
    return _context_var.get()


def clear_context() -> None:
    _context_var.set(None)
