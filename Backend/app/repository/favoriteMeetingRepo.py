import uuid

from app.models.favorite_meeting import FavoriteMeeting
from app.models.group import Group
from app.models.meeting import Meeting
from app.models.member_group_access import MemberGroupAccess
from app.models.user import User
from app.repository.base import BaseRepository


class FavoriteMeetingRepository(BaseRepository):
    def _normalize_uuid(self, value: str):
        try:
            return uuid.UUID(str(value))
        except (ValueError, TypeError):
            return None

    def get_meeting_by_uuid(self, meeting_uuid: str):
        meeting_uuid = self._normalize_uuid(meeting_uuid)
        if not meeting_uuid:
            return None
        return self.session.query(Meeting).filter(Meeting.UUID == meeting_uuid).first()

    def user_can_access_meeting(self, user_uuid: str, meeting_uuid: str, user_role: str) -> bool:
        normalized_user_uuid = self._normalize_uuid(user_uuid)
        normalized_meeting_uuid = self._normalize_uuid(meeting_uuid)
        if not normalized_user_uuid or not normalized_meeting_uuid:
            return False

        meeting = self.get_meeting_by_uuid(str(normalized_meeting_uuid))
        if not meeting:
            return False

        if user_role in {"admin", "super_admin"}:
            return True

        group_uuids = [group.UUID for group in meeting.groups]
        if not group_uuids:
            return False

        access_rows = (
            self.session.query(MemberGroupAccess)
            .filter(
                MemberGroupAccess.member_uuid == normalized_user_uuid,
                MemberGroupAccess.group_uuid.in_(group_uuids),
            )
            .all()
        )
        if not access_rows:
            return False

        if user_role == "viewer":
            return True

        meeting_access = str(getattr(meeting.accessLevel, "value", meeting.accessLevel))
        return any(
            str(getattr(row.access_level, "value", row.access_level)) == meeting_access
            for row in access_rows
        )

    def add_favorite(self, user_uuid: str, meeting_uuid: str):
        normalized_user_uuid = self._normalize_uuid(user_uuid)
        normalized_meeting_uuid = self._normalize_uuid(meeting_uuid)
        if not normalized_user_uuid or not normalized_meeting_uuid:
            return None

        meeting = self.session.query(Meeting).filter(Meeting.UUID == normalized_meeting_uuid).first()
        if not meeting:
            return None

        existing = (
            self.session.query(FavoriteMeeting)
            .filter(
                FavoriteMeeting.member_uuid == normalized_user_uuid,
                FavoriteMeeting.meeting_uuid == normalized_meeting_uuid,
            )
            .first()
        )
        if existing:
            return existing

        favorite = FavoriteMeeting(member_uuid=normalized_user_uuid, meeting_uuid=normalized_meeting_uuid)
        self.session.add(favorite)
        self.session.commit()
        self.session.refresh(favorite)
        return favorite

    def remove_favorite(self, user_uuid: str, meeting_uuid: str) -> bool:
        normalized_user_uuid = self._normalize_uuid(user_uuid)
        normalized_meeting_uuid = self._normalize_uuid(meeting_uuid)
        if not normalized_user_uuid or not normalized_meeting_uuid:
            return False

        favorite = (
            self.session.query(FavoriteMeeting)
            .filter(
                FavoriteMeeting.member_uuid == normalized_user_uuid,
                FavoriteMeeting.meeting_uuid == normalized_meeting_uuid,
            )
            .first()
        )
        if not favorite:
            return False

        self.session.delete(favorite)
        self.session.commit()
        return True

    def get_user_favorites(self, user_uuid: str, user_role: str):
        normalized_user_uuid = self._normalize_uuid(user_uuid)
        if not normalized_user_uuid:
            return []

        favorites = (
            self.session.query(FavoriteMeeting)
            .filter(FavoriteMeeting.member_uuid == normalized_user_uuid)
            .order_by(FavoriteMeeting.created_at.desc())
            .all()
        )

        allowed = []
        for favorite in favorites:
            if self.user_can_access_meeting(str(normalized_user_uuid), str(favorite.meeting_uuid), user_role):
                allowed.append(favorite)
        return allowed

    def get_meeting_participants(self, meeting_uuid: str):
        normalized_meeting_uuid = self._normalize_uuid(meeting_uuid)
        if not normalized_meeting_uuid:
            return []

        users = (
            self.session.query(User)
            .join(MemberGroupAccess, MemberGroupAccess.member_uuid == User.UUID)
            .join(Group, Group.UUID == MemberGroupAccess.group_uuid)
            .join(Group.meetings)
            .filter(Meeting.UUID == normalized_meeting_uuid)
            .distinct()
            .all()
        )
        return users
