from datetime import datetime
from typing import List
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schema.meeting import MeetingRole


class FavoriteMeetingParticipant(BaseModel):
    UUID: UUID
    s_id: str
    username: str

    model_config = ConfigDict(extra="forbid", from_attributes=True)


class FavoriteMeetingOutput(BaseModel):
    m_number: str                                                # מספר הפגישה — המזהה בכל המערכת
    name: str | None = None
    accessLevel: MeetingRole
    password: str | None = None
    groups: List[UUID] = Field(default_factory=list)
    participants: List[FavoriteMeetingParticipant] = Field(default_factory=list)
    favorite_created_at: datetime

    model_config = ConfigDict(extra="forbid", from_attributes=True)


class FavoriteToggleResponse(BaseModel):
    detail: str

    model_config = ConfigDict(extra="forbid", from_attributes=True)
