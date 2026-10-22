from ..logging import PlatformLogger


class ServiceAdapter(PlatformLogger):
    """Service-mode telemetry adapter -- a long-lived process, context bound per
    request via the shared platform_core.telemetry.context module. This is exactly
    PlatformLogger; the name formalizes it as this story's service-mode adapter
    without introducing new behavior (per #249's own implementation notes)."""
