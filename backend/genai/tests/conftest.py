import os

import pytest

from src.logger import logger


def pytest_configure(config):
    # pytest開始時に一度だけ呼び出されるフック
    logger.info("Pytest is starting up...")


@pytest.fixture(scope="session", autouse=True)
def disable_wandb_and_weave():
    os.environ["WANDB_DISABLED"] = "true"
    logger.info("WANDB_DISABLED set to 'true'")

    import weave

    logger.info("Weave is imported")
