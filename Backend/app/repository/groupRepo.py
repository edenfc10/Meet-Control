# ============================================================================
# GroupRepository - ×©×›×‘×ª ×’×™×©×” ×œ× ×ª×•× ×™× ×©×œ ×ž×“×•×¨×™×
# ============================================================================
# ××—×¨××™×ª ×¢×œ ×›×œ ×¤×¢×•×œ×•×ª ×”DB ×©×§×©×•×¨×•×ª ×œ×ž×“×•×¨×™×:
#   - CRUD ×ž×œ× (create/read/update/delete)
#   - × ×™×”×•×œ ×—×‘×¨×™×: ×”×•×¡×¤×”, ×”×¡×¨×”, ×¢×“×›×•×Ÿ ×¨×ž×ª ×’×™×©×”
#   - ניהול פגישות: שיוך פגישה למדור
#
# תהליך הוספת חבר:
#   1. ×‘×•×“×§ ×©×”×ž×“×•×¨ ×•×”×ž×©×ª×ž×© ×§×™×™×ž×™×
#   2. ×× ×”×ž×©×ª×ž×© ×œ× ×—×‘×¨, ×ž×•×¡×™×£ ××•×ª×• ×œ×ž×“×•×¨
#   3. ×ž×•×—×§ ×¨×©×•×ž×ª ×’×™×©×” ×™×©× ×” (×× ×§×™×™×ž×ª) ×•×ž×•×¡×™×£ ×—×“×©×”
# ============================================================================

from .base import BaseRepository
import uuid
from app.models.user import User
from app.models.group import Group
from app.models.meeting import Meeting
from app.models.member_group_access import MemberGroupAccess, MemberGroupAccessLevel
from app.schema.user import GroupInCreate, GroupInUpdate, GroupOutput, UserOutput


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
        """ ×ž×—×–×™×¨ ××ª ×›×œ ×”×ž×“×•×¨×™× """
        return self.session.query(Group).all()

    def get_groups_by_user_uuid(self, user_uuid: str) -> list[GroupOutput]:
        """ מחזיר את כל המדורים שלמשתמש יש בהם הרשאה (דרך member_access_levels) """
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
        """ ×ž×•×¦× ×ž×“×•×¨ ×œ×¤×™ UUID """
        return self.session.query(Group).filter(Group.UUID == group_uuid).first()

    def delete_group(self, group_uuid: str) -> bool:
        """ ×ž×•×—×§ ×ž×“×•×¨ ×œ×¤×™ UUID. ×ž×—×–×™×¨ True ×× ×”×¦×œ×™×— """
        group = self.session.query(Group).filter(Group.UUID == group_uuid).first()
        if group:
            self.session.delete(group)
            self.session.commit()
            return True
        return False

    def update_group(self, group_uuid: str, group_data: GroupInUpdate) -> GroupOutput:
        """ ×ž×¢×“×›×Ÿ ×¤×¨×˜×™ ×ž×“×•×¨ (×œ×ž×©×œ ×©×) - ×¨×§ ×©×“×•×ª ×©× ×©×œ×—×• """
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

    def add_meeting_to_group_by_uuid(self, group_uuid: str, meeting_uuid: str) -> GroupOutput:
        """
        משייך פגישה למדור לפי UUID של שניהם.
        מונע כפילויות — לא מוסיף אם הפגישה כבר שויכה.
        מונע שיוך לקבוצה נוספת — פגישה יכולה להיות משויכת לקבוצה אחת בלבד.
        """
        group = self.session.query(Group).filter(Group.UUID == group_uuid).first()
        meeting = self.session.query(Meeting).filter(Meeting.UUID == meeting_uuid).first()

        if not group or not meeting:
            return None

        # בדיקה: האם הפגישה כבר שויכה לקבוצה אחרת?
        if meeting.groups:
            already_in = [g for g in meeting.groups if str(g.UUID) != str(group_uuid)]
            if already_in:
                from fastapi import HTTPException
                raise HTTPException(
                    status_code=400,
                    detail=f"Meeting is already assigned to group '{already_in[0].name}'. A meeting can only belong to one group."
                )

        if meeting not in group.meetings:
            group.meetings.append(meeting)

        self.session.commit()
        self.session.refresh(group)
        return group

    def remove_meeting_from_group_by_uuid(self, group_uuid: str, meeting_uuid: str) -> GroupOutput:
        """ מסיר שיוך פגישה מקבוצה לפי UUID """
        group = self.session.query(Group).filter(Group.UUID == group_uuid).first()
        meeting = self.session.query(Meeting).filter(Meeting.UUID == meeting_uuid).first()
        if not group or not meeting:
            return None
        if meeting in group.meetings:
            group.meetings.remove(meeting)
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