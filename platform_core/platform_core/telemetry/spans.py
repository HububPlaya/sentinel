import time
from typing import Callable

from .adapters.service import ServiceAdapter


def instrument_call(resource: str, operation: str, call: Callable, *, logger=None):
    """Observes a call to a storage dependency as one more hop in the active trace --
    not propagation (a storage system doesn't participate in that), just visibility:
    did this call succeed, how long did it take. Deliberately records only the
    resource's own identifier, not who owns it -- see #338 for why."""
    logger = logger if logger is not None else ServiceAdapter()
    start = time.perf_counter()

    try:
        result = call()
    except Exception:
        duration_ms = (time.perf_counter() - start) * 1000
        logger.log("info", "storage call", resource=resource, operation=operation, duration_ms=duration_ms, outcome="error")
        raise

    duration_ms = (time.perf_counter() - start) * 1000
    logger.log("info", "storage call", resource=resource, operation=operation, duration_ms=duration_ms, outcome="success")
    return result
