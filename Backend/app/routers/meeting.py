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
from app.schema.meeting import MeetingInCreate, MeetingInUpdate, MeetingOutput, MeetingPasswordUpdate
from app.core.database import get_db
from sqlalchemy.orm import Session
from app.security.TokenValidator import TokenValidator
from app.service.meetingService import MeetingService
from app.models.meeting import AccessLevel
from app.service.cms import CMS
from logger import LoggerManager
from typing import Optional
from app.models.meeting import Meeting
from app.models.user import User
from app.models.meeting_participant_status import MeetingParticipantStatus


meetingRouter = APIRouter()

# הגדרת רמות הרשאה
allow_super_admin_only = TokenValidator(allowed_roles=["super_admin"])
allow_admins_only = TokenValidator(allowed_roles=["admin", "super_admin"])
validator = TokenValidator(allowed_roles=["admin", "super_admin", "agent"])
all_members_validator = TokenValidator(allowed_roles=["admin", "super_admin", "agent"])

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
            responsible_access_level=getattr(user, "responsible_access_level", None),
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

@meetingRouter.get("/live-status", status_code=200)
def get_live_status(session: Session = Depends(get_db), user=Depends(allow_admins_only)):
    try:
        LoggerManager.get_logger().info(
            "User %s:%s with role %s requested live status",
            user.s_id, user.UUID, user.role.value,
        )
        return MeetingService(session=session).get_active_meetings()
    except Exception as error:
        LoggerManager.get_logger().exception(
            "Failed to fetch live status for user %s:%s role=%s. Error: %s",
            user.s_id, user.UUID, user.role.value, str(error),
        )
        raise HTTPException(status_code=500, detail="Internal Server Error")


# --- POST /meetings/create_meeting ---
# יצירת פגישה חדשה — access_level נלקח מגוף הבקשה
@meetingRouter.post("/create_meeting", status_code=200, response_model=MeetingOutput)
def create_meeting_by_access_level(meeting_data: MeetingInCreate, session: Session = Depends(get_db), user=Depends(allow_super_admin_only)):
    user_id = getattr(user, "s_id", "unknown")
    user_uuid = getattr(user, "UUID", "unknown")
    user_role = getattr(user, "role", None)
    user_role_value = getattr(user_role, "value", user_role) or "unknown"
    try:
        LoggerManager.get_logger().info(
            "User %s:%s with role %s is creating a meeting with access level %s",
            user_id, user_uuid, user_role_value, meeting_data.accessLevel,
        )
        return MeetingService(session=session).create_meeting(meeting_data=meeting_data, access_level=meeting_data.accessLevel)
    except ValueError as error:
        LoggerManager.get_logger().warning(
            "Failed to create meeting with access level %s for user %s:%s role=%s. Error: %s",
            meeting_data.accessLevel, user_id, user_uuid, user_role_value, str(error),
        )
        raise HTTPException(status_code=400, detail=str(error))
    except Exception as error:
        LoggerManager.get_logger().exception(
            "Failed to create meeting with access level %s for user %s:%s role=%s. Error: %s",
            meeting_data.accessLevel, user_id, user_uuid, user_role_value, str(error),
        )
        raise HTTPException(status_code=500, detail="Internal Server Error")

# --- GET /meetings/live-status ---
# סטטיסטיקה חיה של שיחות ומשתתפים מה-CMS
@meetingRouter.get("/live-status", status_code=200)
def get_live_status(session: Session = Depends(get_db), user=Depends(allow_admins_only)):
    try:
        LoggerManager.get_logger().info(
            "User %s:%s with role %s requested live status",
            user.s_id, user.UUID, user.role.value,
        )
        return MeetingService(session=session).get_active_meetings()
    except HTTPException as http_error:
        raise http_error
    except Exception as error:
        LoggerManager.get_logger().exception(
            "Failed to fetch live status for user %s:%s role=%s. Error: %s",
            user.s_id, user.UUID, user.role.value, str(error),
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

# --- GET /meetings/{meeting_uuid}/participants ---
# שליפת משתמשים מורשים לוועידה לפי מדורים משויכים (מה-DB)
@meetingRouter.get("/{meeting_uuid}/participants", status_code=200)
def get_meeting_participants(meeting_uuid: str, session: Session = Depends(get_db), user=Depends(all_members_validator)):
    meeting = session.query(Meeting).filter(Meeting.UUID == meeting_uuid).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    meeting_level = str(getattr(meeting.accessLevel, "value", meeting.accessLevel)).lower()
    users_seen = set()
    result = []
    for group in meeting.groups:
        for member_access in group.member_access_levels:
            access_val = str(getattr(member_access.access_level, "value", member_access.access_level)).lower()
            if access_val != meeting_level:
                continue
            u = session.query(User).filter(User.UUID == member_access.member_uuid).first()
            if u and str(u.UUID) not in users_seen:
                users_seen.add(str(u.UUID))
                result.append({
                    "name": f"{u.first_name} {u.last_name}".strip() if hasattr(u, "first_name") else u.s_id,
                    "username": u.s_id,
                    "role": str(getattr(u.role, "value", u.role)),
                    "group": group.name,
                })
    return {"meeting_number": meeting.m_number, "participants": result}

@meetingRouter.get("/{meeting_uuid}/live-participants", status_code=200)
def get_meeting_live_participants(meeting_uuid: str, session: Session = Depends(get_db), user=Depends(all_members_validator)):
    meeting = session.query(Meeting).filter(Meeting.UUID == meeting_uuid).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    meeting_level = str(getattr(meeting.accessLevel, "value", meeting.accessLevel)).lower()
    status_map = {
        str(s.user_uuid): s
        for s in session.query(MeetingParticipantStatus).filter(
            MeetingParticipantStatus.meeting_uuid == meeting_uuid
        ).all()
    }
    users_seen = set()
    result = []
    for group in meeting.groups:
        for member_access in group.member_access_levels:
            access_val = str(getattr(member_access.access_level, "value", member_access.access_level)).lower()
            if access_val != meeting_level:
                continue
            u = session.query(User).filter(User.UUID == member_access.member_uuid).first()
            if u and str(u.UUID) not in users_seen:
                users_seen.add(str(u.UUID))
                st = status_map.get(str(u.UUID))
                if st and st.is_kicked:
                    continue
                result.append({
                    "name": f"{u.first_name} {u.last_name}".strip() if hasattr(u, "first_name") else u.s_id,
                    "legId": str(u.UUID),
                    "username": u.s_id,
                    "state": "connected",
                    "mute": str(st.is_muted).lower() if st else "false",
                    "group": group.name,
                })
    return {"meeting_number": meeting.m_number, "call_id": None, "participants": result}

@meetingRouter.post("/{meeting_uuid}/mute", status_code=200)
def mute_meeting_participant(meeting_uuid: str, body: dict, session: Session = Depends(get_db), user=Depends(allow_admins_only)):
    leg_id = body.get("leg_id")
    call_id = body.get("call_id")
    mute = body.get("mute", True)
    if not leg_id:
        raise HTTPException(status_code=400, detail="leg_id is required")
    cms_success = False
    if call_id:
        try:
            cms = CMS()
            cms_success = cms.mute_participant_by_leg_id(call_id, leg_id, bool(mute))
        except Exception as cms_error:
            LoggerManager.get_logger().warning("CMS mute failed for meeting %s leg %s: %s", meeting_uuid, leg_id, str(cms_error))
    try:
        st = session.query(MeetingParticipantStatus).filter(
            MeetingParticipantStatus.meeting_uuid == meeting_uuid,
            MeetingParticipantStatus.user_uuid == leg_id,
        ).first()
        if st:
            st.is_muted = bool(mute)
        else:
            st = MeetingParticipantStatus(
                meeting_uuid=meeting_uuid,
                user_uuid=leg_id,
                is_muted=bool(mute),
                is_kicked=False,
            )
            session.add(st)
        session.commit()
        return {"success": True, "cms": cms_success}
    except Exception as error:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(error))

@meetingRouter.post("/{meeting_uuid}/kick", status_code=200)
def kick_meeting_participant(meeting_uuid: str, body: dict, session: Session = Depends(get_db), user=Depends(allow_admins_only)):
    leg_id = body.get("leg_id")
    call_id = body.get("call_id")
    if not leg_id:
        raise HTTPException(status_code=400, detail="leg_id is required")
    cms_success = False
    if call_id:
        try:
            cms = CMS()
            cms_success = cms.kick_participant_by_leg_id(call_id, leg_id)
        except Exception as cms_error:
            LoggerManager.get_logger().warning("CMS kick failed for meeting %s leg %s: %s", meeting_uuid, leg_id, str(cms_error))
    try:
        st = session.query(MeetingParticipantStatus).filter(
            MeetingParticipantStatus.meeting_uuid == meeting_uuid,
            MeetingParticipantStatus.user_uuid == leg_id,
        ).first()
        if st:
            st.is_kicked = True
        else:
            st = MeetingParticipantStatus(
                meeting_uuid=meeting_uuid,
                user_uuid=leg_id,
                is_muted=False,
                is_kicked=True,
            )
            session.add(st)
        session.commit()
        return {"success": True, "cms": cms_success}
    except Exception as error:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(error))

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

