# ============================================================================
# Group Router - API routes for group management
# ============================================================================
# פעולות:
#   POST   /groups/create                          - יצירת קבוצה חדשה
#   GET    /groups/all                             - שליפת כל הקבוצות
#   GET    /groups/{uuid}                          - שליפת קבוצה בודדת
#   DELETE /groups/{uuid}                          - מחיקת קבוצה
#   PUT    /groups/{uuid}                          - עדכון קבוצה
#   POST   /groups/{uuid}/add-member/{s_id}        - הוספת חבר + רמת גישה
#   POST   /groups/{uuid}/remove-member/{s_id}     - הסרת חבר
#   POST   /groups/{uuid}/add-meeting/{meeting_uuid} - שיוך פגישה לקבוצה
#
# הרשאות: admin + super_admin בלבד
# ============================================================================

from fastapi import APIRouter, Depends, HTTPException
from app.schema.user import BoolOutput, GroupInCreate, GroupInUpdate, GroupOutput, UserOutput
from app.core.database import get_db
from sqlalchemy.orm import Session
from app.security.TokenValidator import TokenValidator
from app.service.groupService import GroupService
from app.models.member_group_access import MemberGroupAccessLevel
from logger import LoggerManager

groupRouter = APIRouter()

 # הגדרת רמות הרשאה
allow_super_admin_only = TokenValidator(allowed_roles=["super_admin"])
allow_admins_only = TokenValidator(allowed_roles=["admin", "super_admin"])
validator = TokenValidator(allowed_roles=["admin", "super_admin", "agent"])
all_members_validator = TokenValidator(allowed_roles=["admin", "super_admin", "agent", "viewer"])


# --- POST /groups/create ---
@groupRouter.post("/create", status_code=200, response_model=GroupOutput, dependencies=[Depends(allow_admins_only)])
def create_group(group_data: GroupInCreate, session: Session = Depends(get_db)):
    try:
        LoggerManager.get_logger().info("Creating group with name=%s", group_data.name)
        return GroupService(session=session).create_group(group_data=group_data)
    except Exception as error:
        LoggerManager.get_logger().exception("Failed to create group with name=%s. Error: %s", group_data.name, str(error))
        raise HTTPException(status_code=500, detail="Internal Server Error")    
 
@groupRouter.get("/all", status_code=200, response_model=list[GroupOutput])
def get_all_groups(session: Session = Depends(get_db), user=Depends(all_members_validator)):
    try:
        user_role = getattr(user.role, "value", user.role)
        LoggerManager.get_logger().info(
            "User %s:%s with role %s requested all groups",
            user.s_id, user.UUID, user_role,
        )
        if user_role in ("agent", "viewer"):
            return GroupService(session=session).get_groups_by_user_uuid(user_uuid=str(user.UUID))
        return GroupService(session=session).get_all_groups()
    except Exception as error:
        LoggerManager.get_logger().exception(
            "Failed to fetch groups for user %s:%s. Error: %s",
            user.s_id, user.UUID, str(error),
        )
        raise HTTPException(status_code=500, detail="Internal Server Error")
    
@groupRouter.get("/{group_uuid}", status_code=200, response_model=GroupOutput)
def get_group_by_uuid(group_uuid: str, session: Session = Depends(get_db), user=Depends(allow_admins_only)):
    try:
        LoggerManager.get_logger().info(
            "User %s:%s with role %s requested group UUID=%s",
            user.s_id, user.UUID, user.role.value, group_uuid,
        )
        return GroupService(session=session).get_group_by_uuid(group_uuid=group_uuid)
    except HTTPException as http_error:
        raise http_error
    except Exception as error:
        LoggerManager.get_logger().exception(
            "Failed to fetch group UUID=%s. Error: %s", group_uuid, str(error),
        )
        raise HTTPException(status_code=500, detail="Internal Server Error")
    
@groupRouter.delete("/{group_uuid}", status_code=200, response_model=BoolOutput)
def delete_group(group_uuid: str, session: Session = Depends(get_db), user=Depends(allow_admins_only)):
    try:
        LoggerManager.get_logger().info(
            "User %s:%s with role %s is deleting group UUID=%s",
            user.s_id, user.UUID, user.role.value, group_uuid,
        )
        success = GroupService(session=session).delete_group(group_uuid=group_uuid)
        return BoolOutput(success=success)
    except HTTPException as http_error:
        raise http_error
    except Exception as error:
        LoggerManager.get_logger().exception(
            "Failed to delete group UUID=%s. Error: %s", group_uuid, str(error),
        )
        raise HTTPException(status_code=500, detail="Internal Server Error")

@groupRouter.put("/{group_uuid}", status_code=200, response_model=GroupOutput)
def update_group(group_uuid: str, group_data: GroupInUpdate, session: Session = Depends(get_db), user=Depends(allow_admins_only)):
    try:
        LoggerManager.get_logger().info(
            "User %s:%s with role %s is updating group UUID=%s",
            user.s_id, user.UUID, user.role.value, group_uuid,
        )
        return GroupService(session=session).update_group(group_uuid=group_uuid, group_data=group_data)
    except HTTPException as http_error:
        raise http_error
    except Exception as error:
        LoggerManager.get_logger().exception(
            "Failed to update group UUID=%s. Error: %s", group_uuid, str(error),
        )
        raise HTTPException(status_code=500, detail="Internal Server Error")


@groupRouter.get("/{group_uuid}/members", status_code=200, response_model=list[UserOutput])
def get_group_members(group_uuid: str, session: Session = Depends(get_db), user=Depends(validator)):
    try:
        LoggerManager.get_logger().info(
            "User %s:%s with role %s requested members of group UUID=%s",
            user.s_id, user.UUID, user.role.value, group_uuid,
        )
        return GroupService(session=session).get_group_members(group_uuid=group_uuid)
    except HTTPException as http_error:
        raise http_error
    except Exception as error:
        LoggerManager.get_logger().exception(
            "Failed to fetch members of group UUID=%s. Error: %s", group_uuid, str(error),
        )
        raise HTTPException(status_code=500, detail="Internal Server Error")

# --- POST /groups/{uuid}/add-member/{s_id}?access_level=... ---
# מוסיף חבר לקבוצה עם רמת גישה (נשלח כ-query parameter)
@groupRouter.post("/{group_uuid}/add-member/{user_s_id}", status_code=200, response_model=GroupOutput)
def add_member_to_group(
    group_uuid: str,
    user_s_id: str,
    access_level: MemberGroupAccessLevel,
    session: Session = Depends(get_db),
    user=Depends(validator),
):
    try:
        LoggerManager.get_logger().info(
            "User %s:%s with role %s is adding member %s to group UUID=%s with access=%s",
            user.s_id, user.UUID, getattr(user.role, "value", str(user.role)),
            user_s_id, group_uuid, getattr(access_level, "value", str(access_level)),
        )
        user_role = getattr(user.role, "value", str(user.role))
        return GroupService(session=session).add_member_to_group(
            group_uuid=group_uuid,
            user_s_id=user_s_id,
            access_level=access_level,
            requester_uuid=str(user.UUID),
            requester_role=user_role,
        )
    except HTTPException as http_error:
        raise http_error
    except Exception as error:
        LoggerManager.get_logger().exception(
            "Failed to add member %s to group UUID=%s. Error: %s", user_s_id, group_uuid, str(error),
        )
        raise HTTPException(status_code=500, detail="Internal Server Error")

# --- POST /groups/{uuid}/remove-member/{s_id} ---
# מסיר חבר מהקבוצה + מוחק הרשאות גישה שלו
@groupRouter.post("/{group_uuid}/remove-member/{user_s_id}", status_code=200, response_model=GroupOutput)
def remove_member_from_group(group_uuid: str, user_s_id: str, session: Session = Depends(get_db), user=Depends(validator)):
    try:
        LoggerManager.get_logger().info(
            "User %s:%s with role %s is removing member %s from group UUID=%s",
            user.s_id, user.UUID, user.role.value, user_s_id, group_uuid,
        )
        return GroupService(session=session).remove_member_from_group(group_uuid=group_uuid, user_s_id=user_s_id)
    except HTTPException as http_error:
        raise http_error
    except Exception as error:
        LoggerManager.get_logger().exception(
            "Failed to remove member %s from group UUID=%s. Error: %s", user_s_id, group_uuid, str(error),
        )
        raise HTTPException(status_code=500, detail="Internal Server Error")


@groupRouter.post("/{group_uuid}/remove-member-access/{user_s_id}", status_code=200, response_model=GroupOutput)
def remove_member_access_from_group(
    group_uuid: str,
    user_s_id: str,
    access_level: MemberGroupAccessLevel,
    session: Session = Depends(get_db),
    user=Depends(validator),
):
    try:
        LoggerManager.get_logger().info(
            "User %s:%s with role %s is removing access=%s for member %s from group UUID=%s",
            user.s_id,
            user.UUID,
            getattr(user.role, "value", str(user.role)),
            getattr(access_level, "value", str(access_level)),
            user_s_id,
            group_uuid,
        )
        user_role = getattr(user.role, "value", str(user.role))
        return GroupService(session=session).remove_member_access_from_group(
            group_uuid=group_uuid,
            user_s_id=user_s_id,
            access_level=access_level,
            requester_uuid=str(user.UUID),
            requester_role=user_role,
        )
    except HTTPException as http_error:
        raise http_error
    except Exception as error:
        LoggerManager.get_logger().exception(
            "Failed to remove access=%s for member %s from group UUID=%s. Error: %s",
            getattr(access_level, "value", str(access_level)),
            user_s_id,
            group_uuid,
            str(error),
        )
        raise HTTPException(status_code=500, detail="Internal Server Error")

# --- POST /groups/{uuid}/add-meeting/{meeting_uuid} ---
# משייך פגישה קיימת לקבוצה
@groupRouter.post("/{group_uuid}/add-meeting/{meeting_uuid}", status_code=200, response_model=GroupOutput)
def add_meeting_to_group(group_uuid: str, meeting_uuid: str, session: Session = Depends(get_db), user=Depends(allow_admins_only)):
    try:
        LoggerManager.get_logger().info(
            "User %s:%s with role %s is adding meeting UUID=%s to group UUID=%s",
            user.s_id, user.UUID, user.role.value, meeting_uuid, group_uuid,
        )
        return GroupService(session=session).add_meeting_to_group(group_uuid=group_uuid, meeting_uuid=meeting_uuid)
    except HTTPException as http_error:
        raise http_error
    except Exception as error:
        LoggerManager.get_logger().exception(
            "Failed to add meeting UUID=%s to group UUID=%s. Error: %s", meeting_uuid, group_uuid, str(error),
        )
        raise HTTPException(status_code=500, detail="Internal Server Error")

# --- POST /groups/{uuid}/remove-meeting/{meeting_uuid} ---
# מסיר שיוך פגישה מקבוצה
@groupRouter.post("/{group_uuid}/remove-meeting/{meeting_uuid}", status_code=200, response_model=GroupOutput)
def remove_meeting_from_group(group_uuid: str, meeting_uuid: str, session: Session = Depends(get_db), user=Depends(allow_admins_only)):
    try:
        LoggerManager.get_logger().info(
            "User %s:%s with role %s is removing meeting UUID=%s from group UUID=%s",
            user.s_id, user.UUID, user.role.value, meeting_uuid, group_uuid,
        )
        return GroupService(session=session).remove_meeting_from_group(group_uuid=group_uuid, meeting_uuid=meeting_uuid)
    except HTTPException as http_error:
        raise http_error
    except Exception as error:
        LoggerManager.get_logger().exception(
            "Failed to remove meeting UUID=%s from group UUID=%s. Error: %s", meeting_uuid, group_uuid, str(error),
        )
        raise HTTPException(status_code=500, detail="Internal Server Error")
