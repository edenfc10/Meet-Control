from enum import Enum
from typing import List, Optional, Literal
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from uuid import UUID

class UserRole(str, Enum):
    super_admin = "super_admin"
    admin = "admin"
    agent = "agent"

    model_config = ConfigDict(use_enum_values=True)

class MadorInCreate(BaseModel):
    name: str
    model_config = ConfigDict(extra="forbid", from_attributes=True)

class MadorInUpdate(BaseModel):
    name: Optional[str] = None

    model_config = ConfigDict(extra="forbid", from_attributes=True)

class MadorOutput(BaseModel):
    UUID: UUID
    name: str
    members: Optional[List[UUID]] = Field(default_factory=list)
    meetings: Optional[List[UUID]] = Field(default_factory=list)


    model_config = ConfigDict(extra="forbid", from_attributes=True)

class UserInCreate(BaseModel):
    s_id: str
    username: str
    password: str
    role: UserRole
    mador_ids: Optional[List[UUID]] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid", from_attributes=True)

class UserInCreateNoRole(BaseModel):
    s_id: str
    username: str
    password: str
    mador_ids: Optional[List[UUID]] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid", from_attributes=True)
    
class UserOutput(BaseModel):
    UUID: UUID
    s_id: str
    username: str
    role: UserRole
    madors: Optional[List[UUID]] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid", from_attributes=True)

class BoolOutput(BaseModel):
    success: bool
    model_config = ConfigDict(extra="forbid", from_attributes=True)


# Update forward references
UserOutput.model_rebuild()

class UserInLogin(BaseModel):
    s_id: str
    password: str
    model_config = ConfigDict(extra="forbid", from_attributes=True)

class UserJWTData(BaseModel):
    UUID: str
    role: UserRole
    s_id: str

    model_config = ConfigDict(extra="forbid", from_attributes=True)

class UserToken(BaseModel):
    token: str
    role: UserRole

    model_config = ConfigDict(extra="forbid", from_attributes=True)

class UserWithToken(UserOutput):
    token: str

    model_config = ConfigDict(extra="forbid", from_attributes=True)
