"""Process-wide logging setup."""

import logging
import sys
from logging import Logger

LOG_FORMAT = "%(asctime)s %(levelname)-8s %(name)s: %(message)s"


def configure_logging(*, level: str) -> None:
    """Install the root handler every logger in the process writes through."""
    logging.basicConfig(level=level, format=LOG_FORMAT, stream=sys.stdout, force=True)


def create_logger(*, name: str, level: str) -> Logger:
    """Return the named logger at ``level``."""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    return logger
