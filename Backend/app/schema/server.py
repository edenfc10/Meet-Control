from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.meeting import AccessLevel


class ServerInCreate(BaseModel):
    server_name: str = Field(min_length=1, max_length=120)
    ip_address: str = Field(min_length=1, max_length=45)
    username: str = Field(min_length=1, max_length=120)
    password: str = Field(min_length=1, max_length=255)
    accessLevel: AccessLevel

    model_config = ConfigDict(extra="forbid")


class ServerInUpdate(BaseModel):
    server_name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    ip_address: Optional[str] = Field(default=None, min_length=1, max_length=45)
    username: Optional[str] = Field(default=None, min_length=1, max_length=120)
    password: Optional[str] = Field(default=None, min_length=1, max_length=255)
    accessLevel: Optional[AccessLevel] = None

    model_config = ConfigDict(extra="forbid")


class ServerOutput(BaseModel):
    UUID: UUID
    server_name: str
    ip_address: str
    username: str
    password: str
    accessLevel: AccessLevel

    model_config = ConfigDict(from_attributes=True)


