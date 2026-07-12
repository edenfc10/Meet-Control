from fastapi import HTTPException

from app.repository.favoriteMeetingRepo import FavoriteMeetingRepository
from app.schema.favorite import FavoriteMeetingOutput, FavoriteMeetingParticipant
from app.service.cms import CMSFactory
from app.service.meetingService import MeetingService, _clean


class FavoriteMeetingService:
    def __init__(self, session):
        self.session = session
        self._repo = FavoriteMeetingRepository(session=session)
        self._meetings = MeetingService(session=session)

    def _to_output(self, favorite):
        number = favorite.meeting_number
        cms_type = favorite.access_level
        try:
            cs = CMSFactory.get(self.session, cms_type).get_cospace_by_call_id(number)
        except Exception:
            cs = None
        if not cs:
            return None  # הפגישה נמחקה מ-CMS — מדלגים

        users = self._repo.authorized_users(number, cms_type)
        return FavoriteMeetingOutput(
            m_number=number,
            name=_clean(cs.get("name")) or number,
            accessLevel=cms_type,
            password=_clean(cs.get("passcode")),
            groups=self._meetings._groups_for(number, cms_type),
            participants=[
                FavoriteMeetingParticipant(UUID=u.UUID, s_id=u.s_id, username=u.username)
                for u in users
            ],
            favorite_created_at=favorite.created_at,
        )

    def add_favorite(self, user_uuid: str, user_role: str, meeting_number: str):
        cs, cms_type = self._meetings._find_cospace(meeting_number)
        if not cs or not cms_type:
            raise HTTPException(status_code=404, detail="Meeting is not available")
        if not self._repo.user_can_access(user_uuid, meeting_number, cms_type, user_role):
            raise HTTPException(status_code=403, detail="You are not allowed to access this meeting")
        self._meetings._ensure_meeting_exists(meeting_number, cms_type)
        favorite = self._repo.add_favorite(user_uuid=user_uuid, meeting_number=meeting_number, access_level=cms_type)
        if not favorite:
            raise HTTPException(status_code=400, detail="Invalid meeting")
        return favorite

    def remove_favorite(self, user_uuid: str, meeting_number: str) -> bool:
        if self._repo.remove_favorite(user_uuid=user_uuid, meeting_number=meeting_number):
            return True
        raise HTTPException(status_code=404, detail="Favorite meeting was not found")

    def get_user_favorites(self, user_uuid: str, user_role: str):
        favorites = self._repo.get_user_favorites(user_uuid=user_uuid)
        result = []
        for favorite in favorites:
            if not self._repo.user_can_access(user_uuid, favorite.meeting_number, favorite.access_level, user_role):
                continue
            item = self._to_output(favorite)
            if item is not None:
                result.append(item)
        return result
