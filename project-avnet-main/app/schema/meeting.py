from enum import Enum
from typing import List, Optional, Literal
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from uuid import UUID


class MeetingRole(str, Enum):
    audio = "audio"
    video = "video"
    blast_dial = "blast_dial"

    model_config = ConfigDict(use_enum_values=True)

class MeetingInCreate(BaseModel):
    m_number : str
    accessLevel: MeetingRole

class MeetingInUpdate(BaseModel):
    m_number : Optional[str] = None
    accessLevel: Optional[MeetingRole] = None

    model_config = ConfigDict(extra="forbid", from_attributes=True)

class MeetingOutput(BaseModel):
    UUID: UUID
    m_number: str
    accessLevel: MeetingRole
    madors: Optional[List[UUID]] = Field(default_factory=list)
   

    model_config = ConfigDict(extra="forbid", from_attributes=True)