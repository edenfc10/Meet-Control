from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.meeting import AccessLevel


class ServerInCreate(BaseModel):
    server_name: str = Field(min_length=1, max_length=120)
    ip_address: str = Field(min_length=1, max_length=45)
    port: int = Field(ge=1, le=65535)
    username: str = Field(min_length=1, max_length=120)
    password: str = Field(min_length=1, max_length=255)
    accessLevel: AccessLevel
    priority: int = Field(default=1, ge=1)

    model_config = ConfigDict(extra="forbid")


class ServerInUpdate(BaseModel):
    server_name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    ip_address: Optional[str] = Field(default=None, min_length=1, max_length=45)
    port: Optional[int] = Field(default=None, ge=1, le=65535)
    username: Optional[str] = Field(default=None, min_length=1, max_length=120)
    password: Optional[str] = Field(default=None, min_length=1, max_length=255)
    accessLevel: Optional[AccessLevel] = None
    priority: Optional[int] = Field(default=None, ge=1)

    model_config = ConfigDict(extra="forbid")


class ServerOutput(BaseModel):
    UUID: UUID
    server_name: str
    ip_address: str
    port: int
    username: str
    password: str
    accessLevel: AccessLevel
    priority: int
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


