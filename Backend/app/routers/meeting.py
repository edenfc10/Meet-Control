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

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from app.schema.meeting import MeetingInCreate, MeetingInUpdate, MeetingOutput, MeetingPasswordUpdate
from app.core.database import get_db
from sqlalchemy.orm import Session
from app.security.TokenValidator import TokenValidator
from app.service.meetingService import MeetingService
from app.models.meeting import AccessLevel
from logger import LoggerManager
from typing import Optional, Dict
from pydantic import BaseModel

meetingRouter = APIRouter()

# Pydantic models for CMS operations
class ParticipantMuteRequest(BaseModel):
    call_id: str
    participant_name: str
    mute: bool = True
    server_name: Optional[str] = "primary"

class ParticipantKickRequest(BaseModel):
    call_id: str
    participant_name: str
    server_name: Optional[str] = "primary"

class ParticipantLayoutRequest(BaseModel):
    call_id: str
    participant_name: str
    layout: str
    server_name: Optional[str] = "primary"

class CoSpaceCreateRequest(BaseModel):
    name: str
    uri: Optional[str] = None
    passcode: Optional[str] = None
    server_name: Optional[str] = "primary"

class PasscodeUpdateRequest(BaseModel):
    passcode: str
    server_name: Optional[str] = "primary"

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
        user_role = str(getattr(user.role, "value", user.role)).lower().strip()
        LoggerManager.get_logger().info(
            "User %s:%s with role %s requested all meetings with access level=%s",
            user.s_id, user.UUID, user_role, access_level,
        )
        return MeetingService(session=session).get_all_meetings(
            user_uuid=str(user.UUID),
            user_role=user_role,
            access_level=access_level,
        )
    except Exception as error:
        LoggerManager.get_logger().exception(
            "Failed to fetch all meetings for user %s:%s role=%s. Error: %s",
            user.s_id, user.UUID, user_role, str(error),
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
    
@meetingRouter.put("/password/{meeting_uuid}", status_code=200, response_model=MeetingOutput)
def update_meeting_password(meeting_uuid: str, meeting_data: MeetingPasswordUpdate, session: Session = Depends(get_db), user=Depends(validator)):
    try:
        user_role = str(getattr(user.role, "value", user.role)).lower().strip()
        LoggerManager.get_logger().info(
            "User %s:%s with role %s updating password for meeting UUID=%s",
            user.s_id, user.UUID, user_role, meeting_uuid,
        )
        return MeetingService(session=session).update_password_by_uuid(
            meeting_uuid=meeting_uuid,
            password=meeting_data.password,
            user_uuid=str(user.UUID),
            user_role=user_role,
        )
    except HTTPException as http_error:
        raise http_error
    except Exception as error:
        LoggerManager.get_logger().exception(
            "Failed to update meeting password UUID=%s. Error: %s", meeting_uuid, str(error),
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

# ========== CMS Call Management Endpoints ==========

# --- GET /meetings/calls/active ---
# קבלת רשימת שיחות פעילות מ-CMS
@meetingRouter.get("/calls/active", status_code=200)
def get_active_calls(
    server_name: str = Query(default="primary", description="CMS server name"),
    session: Session = Depends(get_db), 
    user=Depends(allow_admins_only)
):
    try:
        LoggerManager.get_logger().info(
            "User %s:%s requested active calls from CMS server %s",
            user.s_id, user.UUID, server_name
        )
        return MeetingService(session=session).get_active_calls(server_name=server_name)
    except Exception as error:
        LoggerManager.get_logger().exception(
            "Failed to get active calls from CMS server %s. Error: %s",
            server_name, str(error)
        )
        raise HTTPException(status_code=500, detail="Internal Server Error")

# --- GET /meetings/calls/{call_id}/participants ---
# קבלת רשימת משתתפים בשיחה ספציפית
@meetingRouter.get("/calls/{call_id}/participants", status_code=200)
def get_call_participants(
    call_id: str,
    server_name: str = Query(default="primary", description="CMS server name"),
    session: Session = Depends(get_db), 
    user=Depends(allow_admins_only)
):
    try:
        LoggerManager.get_logger().info(
            "User %s:%s requested participants for call %s from CMS server %s",
            user.s_id, user.UUID, call_id, server_name
        )
        return MeetingService(session=session).get_call_participants(call_id=call_id, server_name=server_name)
    except Exception as error:
        LoggerManager.get_logger().exception(
            "Failed to get participants for call %s from CMS server %s. Error: %s",
            call_id, server_name, str(error)
        )
        raise HTTPException(status_code=500, detail="Internal Server Error")

# --- POST /meetings/calls/participants/mute ---
# השתקה או ביטול השתקה של משתתף
@meetingRouter.post("/calls/participants/mute", status_code=200)
def mute_participant(
    request: ParticipantMuteRequest,
    session: Session = Depends(get_db), 
    user=Depends(allow_admins_only)
):
    try:
        LoggerManager.get_logger().info(
            "User %s:%s attempting to %s participant %s in call %s on CMS server %s",
            user.s_id, user.UUID, 
            "mute" if request.mute else "unmute",
            request.participant_name, request.call_id, request.server_name
        )
        result = MeetingService(session=session).mute_participant(
            call_id=request.call_id,
            participant_name=request.participant_name,
            mute=request.mute,
            server_name=request.server_name
        )
        return {"success": result, "message": f"Participant {'muted' if request.mute else 'unmuted'} successfully"}
    except Exception as error:
        LoggerManager.get_logger().exception(
            "Failed to %s participant %s in call %s on CMS server %s. Error: %s",
            "mute" if request.mute else "unmute",
            request.participant_name, request.call_id, request.server_name, str(error)
        )
        raise HTTPException(status_code=500, detail="Internal Server Error")

# --- POST /meetings/calls/participants/kick ---
# הוצאת משתתף משיחה
@meetingRouter.post("/calls/participants/kick", status_code=200)
def kick_participant(
    request: ParticipantKickRequest,
    session: Session = Depends(get_db), 
    user=Depends(allow_admins_only)
):
    try:
        LoggerManager.get_logger().info(
            "User %s:%s attempting to kick participant %s from call %s on CMS server %s",
            user.s_id, user.UUID, request.participant_name, request.call_id, request.server_name
        )
        result = MeetingService(session=session).kick_participant(
            call_id=request.call_id,
            participant_name=request.participant_name,
            server_name=request.server_name
        )
        return {"success": result, "message": "Participant kicked successfully"}
    except Exception as error:
        LoggerManager.get_logger().exception(
            "Failed to kick participant %s from call %s on CMS server %s. Error: %s",
            request.participant_name, request.call_id, request.server_name, str(error)
        )
        raise HTTPException(status_code=500, detail="Internal Server Error")

# --- GET /meetings/cms/status ---
# בדיקת חיבור לשרת CMS
@meetingRouter.get("/cms/status", status_code=200)
def test_cms_connection(
    server_name: str = Query(default="primary", description="CMS server name"),
    session: Session = Depends(get_db), 
    user=Depends(all_members_validator)
):
    try:
        LoggerManager.get_logger().info(
            "User %s:%s testing connection to CMS server %s",
            user.s_id, user.UUID, server_name
        )
        result = MeetingService(session=session).test_cms_connection(server_name=server_name)
        return {"connected": result, "server": server_name}
    except Exception as error:
        LoggerManager.get_logger().exception(
            "Failed to test connection to CMS server %s. Error: %s",
            server_name, str(error)
        )
        raise HTTPException(status_code=500, detail="Internal Server Error")

# --- POST /meetings/cospaces ---
# יצירת CoSpace חדש ב-CMS
@meetingRouter.post("/cospaces", status_code=200)
def create_cospace(
    request: CoSpaceCreateRequest,
    session: Session = Depends(get_db), 
    user=Depends(allow_admins_only)
):
    try:
        LoggerManager.get_logger().info(
            "User %s:%s creating CoSpace '%s' on CMS server %s",
            user.s_id, user.UUID, request.name, request.server_name
        )
        result = MeetingService(session=session).create_cospace(
            name=request.name,
            uri=request.uri,
            passcode=request.passcode,
            server_name=request.server_name
        )
        return result
    except Exception as error:
        LoggerManager.get_logger().exception(
            "Failed to create CoSpace '%s' on CMS server %s. Error: %s",
            request.name, request.server_name, str(error)
        )
        raise HTTPException(status_code=500, detail="Internal Server Error")

# --- GET /meetings/cospaces ---
# קבלת רשימת כל ה-CoSpaces ב-CMS
@meetingRouter.get("/cospaces", status_code=200)
def list_cospaces(
    server_name: str = Query(default="primary", description="CMS server name"),
    session: Session = Depends(get_db), 
    user=Depends(allow_admins_only)
):
    try:
        LoggerManager.get_logger().info(
            "User %s:%s requested CoSpaces list from CMS server %s",
            user.s_id, user.UUID, server_name
        )
        return MeetingService(session=session).list_cospaces(server_name=server_name)
    except Exception as error:
        LoggerManager.get_logger().exception(
            "Failed to list CoSpaces from CMS server %s. Error: %s",
            server_name, str(error)
        )
        raise HTTPException(status_code=500, detail="Internal Server Error")

# --- GET /meetings/cospaces/{cospace_id} ---
# קבלת פרטי CoSpace ספציפי מ-CMS
@meetingRouter.get("/cospaces/{cospace_id}", status_code=200)
def get_cospace_details(
    cospace_id: str,
    server_name: str = Query(default="primary", description="CMS server name"),
    session: Session = Depends(get_db), 
    user=Depends(allow_admins_only)
):
    try:
        LoggerManager.get_logger().info(
            "User %s:%s requested CoSpace details for %s from CMS server %s",
            user.s_id, user.UUID, cospace_id, server_name
        )
        return MeetingService(session=session).get_cospace_details(cospace_id=cospace_id, server_name=server_name)
    except Exception as error:
        LoggerManager.get_logger().exception(
            "Failed to get CoSpace details %s from CMS server %s. Error: %s",
            cospace_id, server_name, str(error)
        )
        raise HTTPException(status_code=500, detail="Internal Server Error")

# --- DELETE /meetings/cospaces/{cospace_id} ---
# מחיקת CoSpace מ-CMS
@meetingRouter.delete("/cospaces/{cospace_id}", status_code=200)
def delete_cospace(
    cospace_id: str,
    server_name: str = Query(default="primary", description="CMS server name"),
    session: Session = Depends(get_db), 
    user=Depends(allow_admins_only)
):
    try:
        LoggerManager.get_logger().info(
            "User %s:%s deleting CoSpace %s from CMS server %s",
            user.s_id, user.UUID, cospace_id, server_name
        )
        result = MeetingService(session=session).delete_cospace(cospace_id=cospace_id, server_name=server_name)
        return {"deleted": result, "cospace_id": cospace_id}
    except Exception as error:
        LoggerManager.get_logger().exception(
            "Failed to delete CoSpace %s from CMS server %s. Error: %s",
            cospace_id, server_name, str(error)
        )
        raise HTTPException(status_code=500, detail="Internal Server Error")

# --- PUT /meetings/cospaces/{cospace_id}/passcode ---
# עדכון סיסמת CoSpace ב-CMS
@meetingRouter.put("/cospaces/{cospace_id}/passcode", status_code=200)
def update_cospace_passcode(
    cospace_id: str,
    request: PasscodeUpdateRequest,
    server_name: str = Query(default="primary", description="CMS server name"),
    session: Session = Depends(get_db), 
    user=Depends(allow_admins_only)
):
    try:
        LoggerManager.get_logger().info(
            "User %s:%s updating passcode for CoSpace %s from CMS server %s",
            user.s_id, user.UUID, cospace_id, server_name
        )
        return MeetingService(session=session).update_cospace_passcode(
            cospace_id=cospace_id, 
            passcode=request.passcode, 
            server_name=server_name
        )
    except Exception as error:
        LoggerManager.get_logger().exception(
            "Failed to update passcode for CoSpace %s from CMS server %s. Error: %s",
            cospace_id, server_name, str(error)
        )
        raise HTTPException(status_code=500, detail="Internal Server Error")

# --- GET /meetings/calls/{call_id}/details ---
# קבלת פרטי שיחה ספציפית מ-CMS
@meetingRouter.get("/calls/{call_id}/details", status_code=200)
def get_call_details(
    call_id: str,
    server_name: str = Query(default="primary", description="CMS server name"),
    session: Session = Depends(get_db), 
    user=Depends(allow_admins_only)
):
    try:
        LoggerManager.get_logger().info(
            "User %s:%s requested call details for %s from CMS server %s",
            user.s_id, user.UUID, call_id, server_name
        )
        return MeetingService(session=session).get_call_details(call_id=call_id, server_name=server_name)
    except Exception as error:
        LoggerManager.get_logger().exception(
            "Failed to get call details %s from CMS server %s. Error: %s",
            call_id, server_name, str(error)
        )
        raise HTTPException(status_code=500, detail="Internal Server Error")

# --- GET /meetings/calls/{call_id}/participants/ids ---
# קבלת רשימת מזהי משתתפים בשיחה
@meetingRouter.get("/calls/{call_id}/participants/ids", status_code=200)
def get_participant_ids(
    call_id: str,
    server_name: str = Query(default="primary", description="CMS server name"),
    session: Session = Depends(get_db), 
    user=Depends(allow_admins_only)
):
    try:
        LoggerManager.get_logger().info(
            "User %s:%s requested participant IDs for call %s from CMS server %s",
            user.s_id, user.UUID, call_id, server_name
        )
        return MeetingService(session=session).get_participant_ids(call_id=call_id, server_name=server_name)
    except Exception as error:
        LoggerManager.get_logger().exception(
            "Failed to get participant IDs for call %s from CMS server %s. Error: %s",
            call_id, server_name, str(error)
        )
        raise HTTPException(status_code=500, detail="Internal Server Error")

