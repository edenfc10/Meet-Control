# ============================================================================
# Meeting Router - נתיבי API לניהול פגישות
# ============================================================================
# נתיבים:
#   GET    /meetings/all_access_levels     - שליפת כל הפגישות
#   GET    /meetings/number/{{number}}       - שליפת פגישה לפי מספר
#   GET    /meetings/group/{{group_uuid}}    - רשימת פגישות לפי קבוצה
#   GET    /meetings/{{uuid}}                - שליפת פגישה בודדת לפי UUID
#   POST   /meetings/create_meeting        - יצירת פגישה חדשה
#   DELETE /meetings/{{uuid}}                - מחיקת פגישה
#   PUT    /meetings/{{uuid}}                - עדכון פגישה לפי UUID
#   PUT    /meetings/number/{{number}}       - עדכון פגישה לפי מספר
#
# הרשאות: admin + super_admin בלבד (agent לקריאה בודדת)
# ============================================================================

from fastapi import APIRouter, Depends, HTTPException, Path
from app.schema.meeting import MeetingInCreate, MeetingInUpdate, MeetingOutput
from app.core.database import get_db
from sqlalchemy.orm import Session
from app.security.TokenValidator import TokenValidator
from app.service.meetingService import MeetingService
from app.models.meeting import AccessLevel
from logger import LoggerManager
from typing import Optional

meetingRouter = APIRouter()

# הגדרת רמות הרשאה
allow_super_admin_only = TokenValidator(allowed_roles=["super_admin"])
allow_admins_only = TokenValidator(allowed_roles=["admin", "super_admin"])
validator = TokenValidator(allowed_roles=["admin", "super_admin", "agent"])
all_members_validator = TokenValidator(allowed_roles=["admin", "super_admin", "agent", "viewer"])

# --- GET /meetings/all_access_levels ---
# שליפת כל הפגישות ללא סינון לפי סוג
@meetingRouter.get("/all_meetings", status_code=200, response_model=list[MeetingOutput])
def get_all_meetings(session: Session = Depends(get_db), access_level: Optional[AccessLevel] = None, user=Depends(all_members_validator)):
    try:
        LoggerManager.get_logger().info(
            "User %s:%s with role %s requested all meetings with access level=%s",
            user.s_id, user.UUID, user.role.value, access_level,
        )
        return MeetingService(session=session).get_all_meetings(user_uuid=str(user.UUID), user_role=user.role.value, access_level=access_level)
    except Exception as error:
        LoggerManager.get_logger().exception(
            "Failed to fetch all meetings for user %s:%s role=%s. Error: %s",
            user.s_id, user.UUID, user.role.value, str(error),
        )
        raise HTTPException(status_code=500, detail="Internal Server Error")

# --- GET /meetings/number/{{number}} ---
# שליפת פגישה לפי מספר — חייב להיות לפני /{{meeting_uuid}} כדי שלא יתפס כ-UUID
@meetingRouter.get("/number/{number}", status_code=200, response_model=MeetingOutput)
def get_meeting_by_number(number: int, session: Session = Depends(get_db), user=Depends(allow_admins_only)):
    try:
        LoggerManager.get_logger().info(
            "User %s:%s with role %s requested meeting by number=%s",
            user.s_id, user.UUID, user.role.value, number,
        )
        return MeetingService(session=session).get_meeting_by_number(number=number)
    except HTTPException as http_error:
        raise http_error
    except Exception as error:
        LoggerManager.get_logger().exception(
            "Failed to fetch meeting by number=%s. Error: %s", number, str(error),
        )
        raise HTTPException(status_code=500, detail="Internal Server Error")

# --- GET /meetings/group/{{group_uuid}} ---
# שליפת פגישות לפי קבוצה — חייב להיות לפני /{{meeting_uuid}} כדי שלא יתפס כ-UUID
@meetingRouter.get("/group/{group_uuid}", status_code=200, response_model=list[str])
def get_meetings_by_group_uuid(group_uuid: str, session: Session = Depends(get_db), user=Depends(allow_admins_only)):
    try:
        LoggerManager.get_logger().info(
            "User %s:%s with role %s requested meetings for group UUID=%s",
            user.s_id, user.UUID, user.role.value, group_uuid,
        )
        return MeetingService(session=session).get_meetings_by_group_uuid(group_uuid=group_uuid)
    except HTTPException as http_error:
        raise http_error
    except Exception as error:
        LoggerManager.get_logger().exception(
            "Failed to fetch meetings for group UUID=%s. Error: %s", group_uuid, str(error),
        )
        raise HTTPException(status_code=500, detail="Internal Server Error")


# --- POST /meetings/create_meeting ---
# יצירת פגישה חדשה — access_level נלקח מגוף הבקשה
@meetingRouter.post("/create_meeting", status_code=200, response_model=MeetingOutput)
def create_meeting_by_access_level(meeting_data: MeetingInCreate, session: Session = Depends(get_db), user=Depends(allow_super_admin_only)):
    try:
        LoggerManager.get_logger().info(
            "User %s:%s with role %s is creating a meeting with access level %s",
            user.s_id, user.UUID, user.role.value, meeting_data.accessLevel,
        )
        return MeetingService(session=session).create_meeting(meeting_data=meeting_data, access_level=meeting_data.accessLevel)
    except Exception as error:
        LoggerManager.get_logger().exception(
            "Failed to create meeting with access level %s for user %s:%s role=%s. Error: %s",
            meeting_data.accessLevel, user.s_id, user.UUID, user.role.value, str(error),
        )
        raise HTTPException(status_code=500, detail="Internal Server Error")

# --- DELETE /meetings/{{meeting_uuid}} ---
# מחיקת פגישה לפי UUID
@meetingRouter.delete("/{meeting_uuid}", status_code=200)
def delete_meeting(meeting_uuid: str, session: Session = Depends(get_db), user=Depends(allow_admins_only)):
    try:
        LoggerManager.get_logger().info("Deleting meeting with UUID=%s", meeting_uuid)
        MeetingService(session=session).delete_meeting(meeting_uuid=meeting_uuid)
        return {"detail": "Meeting deleted successfully"}
    except HTTPException as http_error:
        LoggerManager.get_logger().warning(
            "Failed to delete meeting UUID=%s: %s", meeting_uuid, http_error.detail,
        )
        raise http_error
    except Exception as error:
        LoggerManager.get_logger().exception(
            "Failed to delete meeting UUID=%s. Error: %s", meeting_uuid, str(error),
        )
        raise HTTPException(status_code=500, detail="Internal Server Error")

# --- PUT /meetings/{{meeting_uuid}} ---
# עדכון פגישה לפי UUID
@meetingRouter.put("/{meeting_uuid}", status_code=200, response_model=MeetingOutput)
def update_meeting_by_uuid(meeting_uuid: str, meeting_data: MeetingInUpdate, session: Session = Depends(get_db), user=Depends(allow_admins_only)):
    try:
        LoggerManager.get_logger().info("Updating meeting with UUID=%s", meeting_uuid)
        return MeetingService(session=session).update_meeting_by_uuid(meeting_uuid=meeting_uuid, meeting_data=meeting_data)
    except HTTPException as http_error:
        raise http_error
    except Exception as error:
        LoggerManager.get_logger().exception(
            "Failed to update meeting UUID=%s. Error: %s", meeting_uuid, str(error),
        )
        raise HTTPException(status_code=500, detail="Internal Server Error")

# --- PUT /meetings/number/{{meeting_number}} ---
# עדכון פגישה לפי מספר פגישה
@meetingRouter.put("/number/{meeting_number}", status_code=200, response_model=MeetingOutput)
def update_meeting_by_number(meeting_number: str, meeting_data: MeetingInUpdate, session: Session = Depends(get_db), user=Depends(allow_admins_only)):
    try:
        LoggerManager.get_logger().info("Updating meeting with number=%s", meeting_number)
        return MeetingService(session=session).update_meeting_by_number(meeting_number=meeting_number, meeting_data=meeting_data)
    except HTTPException as http_error:
        raise http_error
    except Exception as error:
        LoggerManager.get_logger().exception(
            "Failed to update meeting number=%s. Error: %s", meeting_number, str(error),
        )
        raise HTTPException(status_code=500, detail="Internal Server Error")

# --- GET /meetings/{{meeting_uuid}} ---
# שליפת פגישה בודדת עם בדיקת הרשאות לפי role
@meetingRouter.get("/{meeting_uuid}", status_code=200, response_model=MeetingOutput)
def get_meeting_by_uuid(meeting_uuid: str = Path(..., pattern=r"^[0-9a-fA-F-]{36}$"), session: Session = Depends(get_db), user=Depends(validator)):
    user_role = getattr(user.role, "value", user.role)
    try:
        LoggerManager.get_logger().info(
            "User %s:%s with role %s requested meeting by UUID=%s",
            user.s_id, user.UUID, user_role, meeting_uuid,
        )
        return MeetingService(session=session).get_meeting_by_uuid_for_user(
            meeting_uuid=meeting_uuid,
            user_uuid=str(user.UUID),
            user_role=user_role,
        )
    except HTTPException as http_error:
        LoggerManager.get_logger().warning(
            "User %s:%s with role %s failed to access meeting UUID=%s: %s",
            user.s_id, user.UUID, user_role, meeting_uuid, http_error.detail,
        )
        raise http_error
    except Exception as error:
        LoggerManager.get_logger().exception(
            "Failed to fetch meeting UUID=%s for user %s:%s role=%s. Error: %s",
            meeting_uuid, user.s_id, user.UUID, user_role, str(error),
        )
        raise HTTPException(status_code=500, detail="Internal Server Error")

