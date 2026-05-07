from fastapi import HTTPException

from app.repository.favoriteMeetingRepo import FavoriteMeetingRepository
from app.schema.favorite import FavoriteMeetingOutput, FavoriteMeetingParticipant


class FavoriteMeetingService:
    def __init__(self, session):
        self._repo = FavoriteMeetingRepository(session=session)

    def _to_output(self, favorite) -> FavoriteMeetingOutput:
        meeting = self._repo.get_meeting_by_uuid(str(favorite.meeting_uuid))
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting is not available")

        participants = self._repo.get_meeting_participants(str(meeting.UUID))

        return FavoriteMeetingOutput(
            meeting_uuid=meeting.UUID,
            m_number=meeting.m_number,
            accessLevel=meeting.accessLevel,
            password=getattr(meeting, "password", None),
            groups=[g.UUID for g in meeting.groups],
            participants=[
                FavoriteMeetingParticipant(UUID=p.UUID, s_id=p.s_id, username=p.username)
                for p in participants
            ],
            favorite_created_at=favorite.created_at,
        )

    def add_favorite(self, user_uuid: str, user_role: str, meeting_uuid: str):
        if not self._repo.user_can_access_meeting(user_uuid=user_uuid, meeting_uuid=meeting_uuid, user_role=user_role):
            raise HTTPException(status_code=403, detail="You are not allowed to access this meeting")

        favorite = self._repo.add_favorite(user_uuid=user_uuid, meeting_uuid=meeting_uuid)
        if not favorite:
            raise HTTPException(status_code=400, detail="Invalid meeting UUID")
        return favorite

    def remove_favorite(self, user_uuid: str, meeting_uuid: str) -> bool:
        if self._repo.remove_favorite(user_uuid=user_uuid, meeting_uuid=meeting_uuid):
            return True
        raise HTTPException(status_code=404, detail="Favorite meeting was not found")

    def get_user_favorites(self, user_uuid: str, user_role: str):
        favorites = self._repo.get_user_favorites(user_uuid=user_uuid, user_role=user_role)
        return [self._to_output(favorite) for favorite in favorites]
