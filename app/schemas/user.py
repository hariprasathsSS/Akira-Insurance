"""User-related Pydantic schemas."""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class CurrentUserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    public_id: str
    name: str
    role: str
    email: str


class DemoLoginRequest(BaseModel):
    public_id: str


class DemoLoginResponse(BaseModel):
    message: str
    public_id: str
    role: str
    instruction: str
