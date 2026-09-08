"""Shared base for outbound DTOs."""

from pydantic import BaseModel, ConfigDict


class BaseResponseModel(BaseModel):
    """Serialises to PascalCase while staying snake_case in Python."""

    model_config = ConfigDict(validate_by_name=True)
