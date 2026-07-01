import uuid

from sqlalchemy import String, cast

from app.models.favorite_meeting import FavoriteMeeting
from app.models.meeting import GroupMeeting
from app.models.member_group_access import MemberGroupAccess
from app.models.user import User
from app.repository.base import BaseRepository


class FavoriteMeetingRepository(BaseRepository):
    def _uid(self, value):
        try:
            return uuid.UUID(str(value))
        except (ValueError, TypeError):
            return None

    def _groups_for(self, meeting_number: str, access_level: str):
        return [
            link.group_uuid
            for link in self.session.query(GroupMeeting).filter(
                GroupMeeting.meeting_number == str(meeting_number),
                GroupMeeting.access_level == str(access_level),
            ).all()
        ]

    def user_can_access(self, user_uuid: str, meeting_number: str, access_level: str, user_role: str) -> bool:
        role = str(user_role or "").lower().strip()
        if role in ("admin", "super_admin"):
            return True
        uid = self._uid(user_uuid)
        if not uid:
            return False
        group_uuids = self._groups_for(meeting_number, access_level)
        if not group_uuids:
            return False
        rows = self.session.query(MemberGroupAccess).filter(
            MemberGroupAccess.member_uuid == uid,
            MemberGroupAccess.group_uuid.in_(group_uuids),
        ).all()
        if not rows:
            return False
        if role == "viewer":
            return True
        return any(
            str(getattr(r.access_level, "value", r.access_level)) == str(access_level) for r in rows
        )

    def add_favorite(self, user_uuid: str, meeting_number: str, access_level: str):
        uid = self._uid(user_uuid)
        if not uid:
            return None
        existing = self.session.query(FavoriteMeeting).filter(
            FavoriteMeeting.member_uuid == uid,
            FavoriteMeeting.meeting_number == str(meeting_number),
            FavoriteMeeting.access_level == str(access_level),
        ).first()
        if existing:
            return existing
        favorite = FavoriteMeeting(
            member_uuid=uid, meeting_number=str(meeting_number), access_level=str(access_level),
        )
        self.session.add(favorite)
        self.session.commit()
        self.session.refresh(favorite)
        return favorite

    def remove_favorite(self, user_uuid: str, meeting_number: str, access_level: str | None = None) -> bool:
        uid = self._uid(user_uuid)
        if not uid:
            return False
        q = self.session.query(FavoriteMeeting).filter(
            FavoriteMeeting.member_uuid == uid,
            FavoriteMeeting.meeting_number == str(meeting_number),
        )
        if access_level:
            q = q.filter(FavoriteMeeting.access_level == str(access_level))
        rows = q.all()
        if not rows:
            return False
        for row in rows:
            self.session.delete(row)
        self.session.commit()
        return True

    def get_user_favorites(self, user_uuid: str):
        uid = self._uid(user_uuid)
        if not uid:
            return []
        return (
            self.session.query(FavoriteMeeting)
            .filter(FavoriteMeeting.member_uuid == uid)
            .order_by(FavoriteMeeting.created_at.desc())
            .all()
        )

    def authorized_users(self, meeting_number: str, access_level: str):
        """משתמשים מורשים לפגישה — לפי המדורים המשויכים והסוג."""
        group_uuids = self._groups_for(meeting_number, access_level)
        if not group_uuids:
            return []
        return (
            self.session.query(User)
            .join(MemberGroupAccess, MemberGroupAccess.member_uuid == User.UUID)
            .filter(
                MemberGroupAccess.group_uuid.in_(group_uuids),
                cast(MemberGroupAccess.access_level, String) == str(access_level),
            )
            .distinct()
            .all()
        )
