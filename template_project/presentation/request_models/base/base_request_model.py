"""Shared base for inbound DTOs."""

from pydantic import BaseModel, ConfigDict


class BaseRequestModel(BaseModel):
    """Accepts PascalCase on the wire while staying snake_case in Python."""

    model_config = ConfigDict(validate_by_name=True)
