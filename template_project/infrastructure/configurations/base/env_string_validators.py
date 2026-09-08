"""Config string type that interpolates the deployment environment name."""

import os
from typing import Annotated

from pydantic import BeforeValidator

from template_project.domain.enums.environment import Environment


def insert_env_name(value: str) -> str:
    """Replace ``{env_name}`` with the value of ``APP_ENV_NAME``."""
    return value.replace(
        "{env_name}", os.getenv("APP_ENV_NAME", Environment.LOCAL.value)
    )


EnvNameString = Annotated[str, BeforeValidator(insert_env_name)]
