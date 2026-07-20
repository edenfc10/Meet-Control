# ============================================================================
# GroupRepository - שכבת גישה לנתונים של מדורים
# ============================================================================
# אחראית על כל פעולות הDB שקשורות למדורים:
#   - CRUD מלא (create/read/update/delete)
#   - ניהול חברים: הוספה, הסרה, עדכון רמת גישה
#   - ניהול פגישות: שיוך פגישה למדור
#
# תהליך הוספת חבר:
#   1. בודק שהמדור והמשתמש קיימים
#   2. אם המשתמש לא חבר, מוסיף אותו למדור
#   3. מוחק רשומת גישה ישנה (אם קיימת) ומוסיף חדשה
# ============================================================================

from .base import BaseRepository
import uuid
from app.models.user import User , UserRole
from app.models.group import Group
from app.models.meeting import GroupMeeting
from app.models.member_group_access import MemberGroupAccess, MemberGroupAccessLevel
from app.schema.user import GroupInCreate, GroupInUpdate, GroupOutput, UserOutput
from fastapi import HTTPException

class GroupRepository(BaseRepository):

    def create_group(self, group_data: GroupInCreate) -> GroupOutput:
        """ יוצר מדור חדש בDB """
        data = group_data.model_dump(exclude_none=True)
        new_group = Group(**data)

        self.session.add(new_group)
        self.session.commit()
        self.session.refresh(new_group)
        return new_group

    def get_all_groups(self) -> list[GroupOutput]:
        """ Returns all groups """
        return self.session.query(Group).all()

    def get_groups_by_user_uuid(self, user_uuid: str) -> list[GroupOutput]:
        """ Returns all groups for a user (via member_access_levels) """
        try:
            normalized_user_uuid = uuid.UUID(str(user_uuid))
        except (ValueError, TypeError):
            return []

        access_rows = self.session.query(MemberGroupAccess).filter(MemberGroupAccess.member_uuid == normalized_user_uuid).all()
        group_uuids = [row.group_uuid for row in access_rows]
        if not group_uuids:
            return []
        return self.session.query(Group).filter(Group.UUID.in_(group_uuids)).all()

    def get_group_by_uuid(self, group_uuid: str) -> GroupOutput:
        """ מוצא מדור לפי UUID """
        return self.session.query(Group).filter(Group.UUID == group_uuid).first()

    def delete_group(self, group_uuid: str) -> bool:
        """ מוחק מדור לפי UUID. מחזיר True אם הצליח """
        group = self.session.query(Group).filter(Group.UUID == group_uuid).first()
        if group:
            self.session.delete(group)
            self.session.commit()
            return True
        return False

    def update_group(self, group_uuid: str, group_data: GroupInUpdate) -> GroupOutput:
        """ Updates a group (by UUID) """
        group = self.session.query(Group).filter(Group.UUID == group_uuid).first()
        if not group:
            return None

        for key, value in group_data.model_dump(exclude_none=True).items():
            setattr(group, key, value)

        self.session.commit()
        self.session.refresh(group)
        return group

    def _find_user(self, identifier: str):
        """ מחפש משתמש לפי s_id קודם, ואם לא נמצא — לפי UUID """
        user = self.session.query(User).filter(User.s_id == identifier).first()
        if not user:
            try:
                user_uuid = uuid.UUID(str(identifier))
                user = self.session.query(User).filter(User.UUID == user_uuid).first()
            except (ValueError, TypeError):
                pass
        return user

    def add_member_to_group(
        self,
        group_uuid: str,
        user_s_id: str,
        access_level: MemberGroupAccessLevel,
    ) -> GroupOutput:
        """
        מוסיף חבר למדור עם רמת גישה מסוימת (דרך MemberGroupAccess).
        מקבל s_id או UUID של המשתמש.
        אם כבר קיים - לא מוסיף כפילות.
        """
        group = self.session.query(Group).filter(Group.UUID == group_uuid).first()
        user = self._find_user(user_s_id)

        if not group or not user:
            return None

        if getattr(user.role, "value", user.role) == "agent":
            other_group = self.session.query(MemberGroupAccess).filter(
                MemberGroupAccess.member_uuid == user.UUID,
                MemberGroupAccess.group_uuid != group.UUID,
            ).first()
            if other_group:
                raise HTTPException(status_code=400, detail="Agent can only belong to one group")

        existing = self.session.query(MemberGroupAccess).filter(
            MemberGroupAccess.member_uuid == user.UUID,
            MemberGroupAccess.group_uuid == group.UUID,
            MemberGroupAccess.access_level == access_level,
        ).first()

        if not existing:
            self.session.add(
                MemberGroupAccess(
                    member_uuid=user.UUID,
                    group_uuid=group.UUID,
                    access_level=access_level,
                )
            )
            self.session.commit()
            self.session.refresh(group)
        return group
    
    def is_user_member_of_group(self, user_uuid: str, group_uuid: str) -> bool:
        """ בודק אם משתמש שייך לקבוצה מסוימת (לפי UUID) """
        try:
            normalized_uuid = uuid.UUID(str(user_uuid))
        except (ValueError, TypeError):
            return False
        row = self.session.query(MemberGroupAccess).filter(
            MemberGroupAccess.member_uuid == normalized_uuid,
            MemberGroupAccess.group_uuid == group_uuid,
        ).first()
        return row is not None

    def get_user_by_s_id(self, s_id: str):
        """ מחזיר משתמש לפי s_id """
        return self.session.query(User).filter(User.s_id == s_id).first()



    def remove_member_from_group(self, group_uuid: str, user_s_id: str) -> GroupOutput:
        """
        מסיר את כל הרשאות החבר מהמדור.
        מקבל s_id או UUID של המשתמש.
        """
        group = self.session.query(Group).filter(Group.UUID == group_uuid).first()
        user = self._find_user(user_s_id)

        if not group or not user:
            return None

        self.session.query(MemberGroupAccess).filter(
            MemberGroupAccess.member_uuid == user.UUID,
            MemberGroupAccess.group_uuid == group.UUID,
        ).delete()
        self.session.commit()
        self.session.refresh(group)
        return group

    def remove_member_access_from_group(
        self,
        group_uuid: str,
        user_s_id: str,
        access_level: MemberGroupAccessLevel,
    ) -> GroupOutput:
        """
        מסיר למשתמש הרשאת גישה ספציפית מהמדור (ולא מסיר אותו לגמרי מכל הסוגים).
        """
        group = self.session.query(Group).filter(Group.UUID == group_uuid).first()
        user = self._find_user(user_s_id)

        if not group or not user:
            return None

        self.session.query(MemberGroupAccess).filter(
            MemberGroupAccess.member_uuid == user.UUID,
            MemberGroupAccess.group_uuid == group.UUID,
            MemberGroupAccess.access_level == access_level,
        ).delete()

        self.session.commit()
        self.session.refresh(group)
        return group

    def add_meeting_to_group_by_number(self, group_uuid: str, meeting_number: str, access_level: str) -> GroupOutput:
        """
        משייך פגישה למדור לפי (מספר + סוג).
        מונע כפילויות ומונע שיוך לקבוצה נוספת — פגישה משויכת למדור אחד בלבד.
        """
        group = self.session.query(Group).filter(Group.UUID == group_uuid).first()
        if not group:
            return None

        num = str(meeting_number)
        lvl = str(access_level)
        existing = self.session.query(GroupMeeting).filter(
            GroupMeeting.meeting_number == num,
            GroupMeeting.access_level == lvl,
            GroupMeeting.group_uuid == group.UUID,
        ).first()
        if existing:
            return group  # already linked to this group

        self.session.add(GroupMeeting(meeting_number=num, access_level=lvl, group_uuid=group.UUID))
        self.session.commit()
        self.session.refresh(group)
        return group

    def remove_meeting_from_group_by_number(self, group_uuid: str, meeting_number: str, access_level: str | None = None) -> GroupOutput:
        """ מסיר שיוך פגישה מקבוצה לפי מספר (ואם ידוע — גם סוג) """
        group = self.session.query(Group).filter(Group.UUID == group_uuid).first()
        if not group:
            return None
        q = self.session.query(GroupMeeting).filter(
            GroupMeeting.meeting_number == str(meeting_number),
            GroupMeeting.group_uuid == group.UUID,
        )
        if access_level:
            q = q.filter(GroupMeeting.access_level == str(access_level))
        q.delete()
        self.session.commit()
        self.session.refresh(group)
        return group

    def get_group_members(self, group_uuid: str) -> list[UserOutput]:
        """ מחזיר את כל המשתמשים שיש להם גישה למדור מסוים (דרך member_access_levels) """
        group = self.session.query(Group).filter(Group.UUID == group_uuid).first()
        if not group:
            return []
        member_uuids = [m.member_uuid for m in group.member_access_levels]
        if not member_uuids:
            return []
        return self.session.query(User).filter(User.UUID.in_(member_uuids)).all()