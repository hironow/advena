import os

import google.auth
import pytest
from google.auth.credentials import AnonymousCredentials

from src.logger import logger

_test_auth = pytest.MonkeyPatch()


def _anonymous_credentials(
    *args: object, **kwargs: object
) -> tuple[AnonymousCredentials, str]:
    return AnonymousCredentials(), "test-project"


def pytest_unconfigure(config: pytest.Config) -> None:
    _test_auth.undo()


def pytest_configure(config: pytest.Config) -> None:
    # Cloud calls are replaced in individual tests; client construction needs
    # credentials before collection and must never read the developer's ADC.
    _test_auth.setattr(google.auth, "default", _anonymous_credentials)
    # pytest開始時に一度だけ呼び出されるフック
    logger.info("Pytest is starting up...")


@pytest.fixture(scope="session", autouse=True)
def disable_wandb_and_weave():
    os.environ["WANDB_DISABLED"] = "true"
    os.environ["WANDB_SILENT"] = "true"
    os.environ["WANDB_MODE"] = "offline"
    logger.info("Wandb is disabled")

    import weave

    logger.info("Weave is imported")
