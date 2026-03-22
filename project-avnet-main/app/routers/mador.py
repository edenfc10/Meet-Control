from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.schema.user import MadorOutput, MadorBase, MeetingOutput, MeetingBase
from app.core.database import get_db
from app.service.madorService import MadorService
from app.service.meetingService import MeetingService
from app.security.TokenValidator import TokenValidator

madorRouter = APIRouter()

# TokenValidator for admin and super_admin roles
admin_validator = TokenValidator(allowed_roles=["admin", "super_admin"])
super_admin_validator = TokenValidator(allowed_roles=["super_admin"])
validator = TokenValidator(allowed_roles=["admin", "super_admin", "agent"])

@madorRouter.post("/", response_model=MadorOutput)
def create_mador(
    mador: MadorBase,
    session: Session = Depends(get_db),
    user = Depends(super_admin_validator)
):
    return MadorService(session=session).create_mador(mador_data=mador, creator_id=user.UUID)


@madorRouter.get("/", response_model=list[MadorOutput])
def list_madors(session: Session = Depends(get_db), user = Depends(validator)):
    return MadorService(session=session).list_madors()


@madorRouter.post("/{mador_id}/members/{user_id}", response_model=MadorOutput)
def add_member(
    mador_id: UUID,
    user_id: UUID,
    session: Session = Depends(get_db),
    user = Depends(admin_validator),
):
    return MadorService(session=session).add_user_to_mador(mador_id=mador_id, user_id=str(user_id), current_user_id=user.UUID)


@madorRouter.delete("/{mador_id}/members/{user_id}", response_model=MadorOutput)
def remove_member(
    mador_id: UUID,
    user_id: UUID,
    session: Session = Depends(get_db),
    user = Depends(admin_validator),
):
    return MadorService(session=session).remove_user_from_mador(mador_id=mador_id, user_id=str(user_id), current_user_id=user.UUID)


@madorRouter.post("/{mador_id}/meetings", response_model=MeetingOutput)
def create_meeting(
    mador_id: UUID,
    meeting: MeetingBase,
    session: Session = Depends(get_db),
    user = Depends(admin_validator),
):
    return MeetingService(session=session).create_meeting(meeting_data=meeting, mador_id=mador_id)


@madorRouter.get("/{mador_id}/meetings", response_model=list[MeetingOutput])
def list_meetings(
    mador_id: UUID,
    session: Session = Depends(get_db),
    user = Depends(validator),
):
    return MeetingService(session=session).get_meetings_by_mador(mador_id=mador_id)
