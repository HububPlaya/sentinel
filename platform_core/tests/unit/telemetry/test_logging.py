import pytest

from platform_core.telemetry.context import clear_context
from platform_core.telemetry.logging import MissingRequiredFieldError, PlatformLogger


def test_raises_when_no_context_and_no_explicit_fields():
    clear_context()
    logger = PlatformLogger()

    with pytest.raises(MissingRequiredFieldError):
        logger.info("payment processed")
