# ============================================================================
# UserRepository - שכבת גישה לנתונים של משתמשים
# ============================================================================
# אחראית על כל פעולות הDB הקשורות למשתמשים:
#   - יצירת משתמש (agent/admin)
#   - שליפת משתמש לפי s_id
#   - קבלת כל המשתמשים
#   - מחיקת משתמש
#   - שליפת פגישות מדור לפי רמת גישה של משתמש
#
# Pattern: Repository Pattern
#   השכבה הזו מדברת רק עם הDB דרך SQLAlchemy.
#   הService משתמש ברפוזיטורי ומוסיף לוגיקה עסקית.
# ============================================================================

import uuid

from .base import BaseRepository
from app.models.user import User
from app.models.group import Group
from app.models.meeting import GroupMeeting

from app.schema.user import UserInCreate, UserInCreateNoRole, UserOutput
from app.models.member_group_access import MemberGroupAccess, MemberGroupAccessLevel


class UserRepository(BaseRepository):

    def create_user(self, user_data: UserInCreate) -> UserOutput:
        """  יוצר משתמש חדש בDB ומשייך אותו למדורים אם צוינו """
        data = user_data.model_dump(exclude_none=True)

       
        data.pop("group_ids", None)

        new_user = User(**data)

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

    def get_user_by_s_id(self, s_id: str) -> UserOutput:
        """ מוצא משתמש לפי מזהה המשתמש (s_id) """
        user = self.session.query(User).filter_by(s_id=s_id).first()
        return user
    
    def get_user_by_uuid(self, uuid: str) -> UserOutput:
        """ מוצא משתמש לפי מזהה המשתמש (UUID) """
        user = self.session.query(User).filter_by(UUID=uuid).first()
        return user


    def get_all_users(self) -> list[UserOutput]:
        """ מחזיר את כל המשתמשים במערכת """
        users = self.session.query(User).all()
        return users

    def get_users_in_same_groups(self, user_uuid: str) -> list[UserOutput]:
        """
        מחזיר משתמשים שחולקים לפחות מדור אחד עם המשתמש הנתון.
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
        """ מוחק משתמש לפי s_id. מחזיר True אם הצליח """
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
        מחזיר רשימת הפגישות שמשתמש רשאי לראות במדור מסוים.
        הלוגיקה:
          1. שולף את רמות הגישה של המשתמש במדור מטבלת member_group_access
          2. מסנן את כל הפגישות שה-accessLevel שלהן תואם לרמת הגישה
        זה מאפשר לסוכן agent לראות רק פגישות שהוא הורשה לראות.
        """
        # שליפת הקשרים של המשתמש במדור הנתון
        connections = self.session.query(MemberGroupAccess).filter(MemberGroupAccess.member_uuid == user_uuid, MemberGroupAccess.group_uuid == group_uuid).all()
        # יצירת רשימת רמות הגישה המותרות
        access_allowed = {str(getattr(conn.access_level, "value", conn.access_level)) for conn in connections}

        # סינון פגישות - מחזיר רק פגישות שהסוג שלהן תואם לרמת הגישה
        links = self.session.query(GroupMeeting).filter(GroupMeeting.group_uuid == group_uuid).all()
        return [link.meeting_number for link in links if link.access_level in access_allowed]
