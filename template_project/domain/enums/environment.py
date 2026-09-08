"""Deployment environments the service runs in."""

from enum import Enum


class Environment(str, Enum):
    """Named deployment targets."""

    LOCAL: str = "local"
    DEV: str = "dev"
    TEST: str = "test"
    PROD: str = "prod"
