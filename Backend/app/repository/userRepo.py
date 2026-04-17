# ============================================================================
# UserRepository - ×©×›×‘×ª ×’×™×©×” ×œ× ×ª×•× ×™× ×©×œ ×ž×©×ª×ž×©×™×
# ============================================================================
# ××—×¨××™×ª ×¢×œ ×›×œ ×¤×¢×•×œ×•×ª ×”DB ×”×§×©×•×¨×•×ª ×œ×ž×©×ª×ž×©×™×:
#   - יצירת משתמש (agent/admin)
#   - שליפת משתמש לפי s_id
#   - ×§×‘×œ×ª ×›×œ ×”×ž×©×ª×ž×©×™×
#   - מחיקת משתמש
#   - שליפת פגישות מדור לפי רמת גישה של משתמש
#
# Pattern: Repository Pattern
#   ×”×©×›×‘×” ×”×–×• ×ž×“×‘×¨×ª ×¨×§ ×¢× ×”DB ×“×¨×š SQLAlchemy.
#   הService משתמש ברפוזיטורי ומוסיף לוגיקה עסקית.
# ============================================================================

import uuid

from .base import BaseRepository
from app.models.user import User
from app.models.group import Group

from app.schema.user import UserInCreate, UserInCreateNoRole, UserOutput
from app.models.member_group_access import MemberGroupAccess, MemberGroupAccessLevel


class UserRepository(BaseRepository):

    def create_user(self, user_data: UserInCreate) -> UserOutput:
        """  ×™×•×¦×¨ ×ž×©×ª×ž×© ×—×“×© ×‘DB ×•×ž×©×™×™×š ××•×ª×• ×œ×ž×“×•×¨×™× ×× ×¦×•×™× ×• """
        data = user_data.model_dump(exclude_none=True)

        # ×ž×•×¦×™× ××ª ×¨×©×™×ž×ª ×”×ž×“×•×¨×™× ×ž×”data ×œ×¤× ×™ ×™×¦×™×¨×ª ×”×™×•×–×¨
        group_ids = data.pop("group_ids", [])

        new_user = User(**data)

        # ×× ×¦×•×™× ×• ×ž×“×•×¨×™× - ×ž×©×™×™×š ××ª ×”×ž×©×ª×ž×© ××œ×™×”×
        if group_ids and len(group_ids) > 0:
            groups = self.session.query(Group).filter(Group.UUID.in_(group_ids)).all()
            new_user.groups.extend(groups)

        self.session.add(new_user)
        self.session.commit()
        self.session.refresh(new_user)

        return new_user
    
    def create_agent_user(self, user_data: UserInCreateNoRole):
        """ יוצר משתמש עם תפקיד agent אוטומטית """
        base = user_data.model_dump(exclude_none=True)
        base["role"] = "agent"
        return self.create_user(UserInCreate(**base))

    def create_admin_user(self, user_data: UserInCreateNoRole):
        """ יוצר משתמש עם תפקיד admin אוטומטית """
        base = user_data.model_dump(exclude_none=True)
        base["role"] = "admin"
        return self.create_user(UserInCreate(**base))

    def create_viewer_user(self, user_data: UserInCreateNoRole):
        """ יוצר משתמש עם תפקיד viewer אוטומטית """
        base = user_data.model_dump(exclude_none=True)
        base["role"] = "viewer"
        return self.create_user(UserInCreate(**base))
    
    def get_user_by_s_id(self, s_id: str) -> UserOutput:
        """ ×ž×•×¦× ×ž×©×ª×ž×© ×œ×¤×™ ×ž×–×”×” ×”×ž×©×ª×ž×© (s_id) """
        user = self.session.query(User).filter_by(s_id=s_id).first()
        return user
    
    def get_user_by_uuid(self, uuid: str) -> UserOutput:
        """ ×ž×•×¦× ×ž×©×ª×ž×© ×œ×¤×™ ×ž×–×”×” ×”×ž×©×ª×ž×© (UUID) """
        user = self.session.query(User).filter_by(UUID=uuid).first()
        return user


    def get_all_users(self) -> list[UserOutput]:
        """ ×ž×—×–×™×¨ ××ª ×›×œ ×”×ž×©×ª×ž×©×™× ×‘×ž×¢×¨×›×ª """
        users = self.session.query(User).all()
        return users

    def get_users_in_same_groups(self, user_uuid: str) -> list[UserOutput]:
        """
        ×ž×—×–×™×¨ ×ž×©×ª×ž×©×™× ×©×—×•×œ×§×™× ×œ×¤×—×•×ª ×ž×“×•×¨ ××—×“ ×¢× ×”×ž×©×ª×ž×© ×”× ×ª×•×Ÿ.
        """
        try:
            normalized_user_uuid = uuid.UUID(str(user_uuid))
        except (ValueError, TypeError):
            return []

        user = self.session.query(User).filter(User.UUID == normalized_user_uuid).first()
        if not user:
            return []

        group_ids = [m.group.UUID for m in user.group_access_levels]
        if not group_ids:
            return [user]

        users = (
            self.session.query(User)
            .join(MemberGroupAccess, MemberGroupAccess.member_uuid == User.UUID)
            .join(Group, Group.UUID == MemberGroupAccess.group_uuid)
            .filter(Group.UUID.in_(group_ids))
            .distinct()
            .all()
        )
        return users

    def delete_user(self, user_id: str) -> bool:
        """ ×ž×•×—×§ ×ž×©×ª×ž×© ×œ×¤×™ s_id. ×ž×—×–×™×¨ True ×× ×”×¦×œ×™×— """
        user = self.session.query(User).filter_by(s_id=user_id).first()
        if user:
            self.session.delete(user)
            self.session.commit()
            return True
    
        return False
    
    def update_details_on_user(self, user_uuid: str, update_data: UserInCreateNoRole) -> UserOutput:
        user = self.session.query(User).filter_by(UUID=user_uuid).first()
        if not user:
            return None

        # המרה לדיקשנרי והסרת ערכי None
        update_dict = update_data.model_dump(exclude_none=True)
        
        for key, value in update_dict.items():
            setattr(user, key, value)

        try:
            self.session.commit()
            self.session.refresh(user)
            return user
        except Exception as e:
            self.session.rollback() # חשוב מאוד למקרה של שגיאה!
            raise e

    def get_group_meetings_by_user_uuid(self, user_uuid: str, group_uuid: str) -> list[str]:
        """
        ×ž×—×–×™×¨ ×¨×©×™×ž×ª ×”×¤×’×™×©×•×ª ×©×ž×©×ª×ž×© ×¨×©××™ ×œ×¨××•×ª ×‘×ž×“×•×¨ ×ž×¡×•×™×.
        הלוגיקה:
          1. ×©×•×œ×£ ××ª ×¨×ž×•×ª ×”×’×™×©×” ×©×œ ×”×ž×©×ª×ž×© ×‘×ž×“×•×¨ ×ž×˜×‘×œ×ª member_group_access
          2. ×ž×¡× ×Ÿ ××ª ×›×œ ×”×¤×’×™×©×•×ª ×©×”-accessLevel ×©×œ×”×Ÿ ×ª×•×× ×œ×¨×ž×ª ×”×’×™×©×”
        ×–×” ×ž××¤×©×¨ ×œ×¡×•×›×Ÿ agent ×œ×¨××•×ª ×¨×§ ×¤×’×™×©×•×ª ×©×”×•× ×”×•×¨×©×” ×œ×¨××•×ª.
        """
        # ×©×œ×™×¤×ª ×”×§×©×¨×™× ×©×œ ×”×ž×©×ª×ž×© ×‘×ž×“×•×¨ ×”× ×ª×•×Ÿ
        connections = self.session.query(MemberGroupAccess).filter(MemberGroupAccess.member_uuid == user_uuid, MemberGroupAccess.group_uuid == group_uuid).all()
        # יצירת רשימת רמות הגישה המותרות
        access_allowed = [conn.access_level for conn in connections]

        # ×¡×™× ×•×Ÿ ×¤×’×™×©×•×ª - ×ž×—×–×™×¨ ×¨×§ ×¤×’×™×©×•×ª ×©×”×¡×•×’ ×©×œ×”×Ÿ ×ª×•×× ×œ×¨×ž×ª ×”×’×™×©×”
        meetings = self.session.query(Group).filter(Group.UUID == group_uuid).first().meetings
        return [str(meeting.UUID) for meeting in meetings if meeting.accessLevel in access_allowed]
