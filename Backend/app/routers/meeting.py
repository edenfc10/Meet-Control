# ============================================================================
# Meeting Router - נתיבי API לניהול פגישות (מבוסס CMS)
# ============================================================================
# הפגישות מנוהלות אך ורק ב-CMS. הזהות בכל הנתיבים היא מספר הפגישה (m_number).
#
#   GET    /meetings/all_meetings            - כל הפגישות (מסונן ל-agent)
#   GET    /meetings/number/{number}         - פגישה לפי מספר
#   GET    /meetings/group/{group_uuid}      - מספרי פגישות של מדור
#   GET    /meetings/live-status             - סטטיסטיקה חיה מה-CMS
#   POST   /meetings/create_meeting          - יצירת פגישה (ב-CMS)
#   DELETE /meetings/{meeting_number}        - מחיקת פגישה (מ-CMS + ניקוי overlay)
#   PUT    /meetings/password/{meeting_number} - עדכון סיסמה (ב-CMS)
#   GET    /meetings/{meeting_number}/participants      - משתמשים מורשים (DB)
#   GET    /meetings/{meeting_number}/live-participants - משתתפים חיים (CMS)
#   POST   /meetings/{meeting_number}/mute|kick         - השתקה/הסרה live (CMS)
#   GET    /meetings/{meeting_number}         - פגישה בודדת לפי הרשאות
# ============================================================================

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schema.meeting import MeetingInCreate, MeetingOutput, MeetingPasswordUpdate, MeetingNameUpdate
from app.security.TokenValidator import TokenValidator
from app.service.meetingService import MeetingService
from app.service.cms import CMS
from app.models.meeting import AccessLevel
from app.models.group import Group
from app.models.user import User
from logger import LoggerManager


meetingRouter = APIRouter()

allow_super_admin_only = TokenValidator(allowed_roles=["super_admin"])
allow_admins_only = TokenValidator(allowed_roles=["admin", "super_admin"])
validator = TokenValidator(allowed_roles=["admin", "super_admin", "agent"])
all_members_validator = TokenValidator(allowed_roles=["admin", "super_admin", "agent"])


# --- GET /meetings/all_meetings ---
@meetingRouter.get("/all_meetings", status_code=200, response_model=list[MeetingOutput])
def get_all_meetings(session: Session = Depends(get_db), access_level: Optional[AccessLevel] = None, user=Depends(all_members_validator)):
    user_role = str(getattr(user.role, "value", user.role)).lower().strip()
    try:
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


# --- GET /meetings/number/{number} ---
@meetingRouter.get("/number/{number}", status_code=200, response_model=MeetingOutput)
def get_meeting_by_number(number: str, session: Session = Depends(get_db), user=Depends(allow_admins_only)):
    try:
        LoggerManager.get_logger().info(
            "User %s:%s requested meeting by number=%s", user.s_id, user.UUID, number,
        )
        return MeetingService(session=session).get_meeting_by_number(number=number)
    except HTTPException:
        raise
    except Exception as error:
        LoggerManager.get_logger().exception("Failed to fetch meeting by number=%s. Error: %s", number, str(error))
        raise HTTPException(status_code=500, detail="Internal Server Error")


# --- GET /meetings/group/{group_uuid} ---
@meetingRouter.get("/group/{group_uuid}", status_code=200, response_model=list[str])
def get_meetings_by_group_uuid(group_uuid: str, session: Session = Depends(get_db), user=Depends(allow_admins_only)):
    try:
        return MeetingService(session=session).get_meetings_by_group_uuid(group_uuid=group_uuid)
    except HTTPException:
        raise
    except Exception as error:
        LoggerManager.get_logger().exception("Failed to fetch meetings for group UUID=%s. Error: %s", group_uuid, str(error))
        raise HTTPException(status_code=500, detail="Internal Server Error")


# --- GET /meetings/live-status ---
@meetingRouter.get("/live-status", status_code=200)
def get_live_status(session: Session = Depends(get_db), user=Depends(allow_admins_only)):
    try:
        return MeetingService(session=session).get_active_meetings()
    except Exception as error:
        LoggerManager.get_logger().exception("Failed to fetch live status. Error: %s", str(error))
        raise HTTPException(status_code=500, detail="Internal Server Error")


# --- POST /meetings/create_meeting ---
@meetingRouter.post("/create_meeting", status_code=200, response_model=MeetingOutput)
def create_meeting_by_access_level(meeting_data: MeetingInCreate, session: Session = Depends(get_db), user=Depends(allow_super_admin_only)):
    user_id = getattr(user, "s_id", "unknown")
    try:
        LoggerManager.get_logger().info(
            "User %s is creating a meeting %s (access level %s)",
            user_id, meeting_data.m_number, meeting_data.accessLevel,
        )
        return MeetingService(session=session).create_meeting(meeting_data=meeting_data, access_level=meeting_data.accessLevel)
    except HTTPException:
        raise
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))
    except Exception as error:
        LoggerManager.get_logger().exception("Failed to create meeting %s: %s", meeting_data.m_number, str(error))
        raise HTTPException(status_code=502, detail=f"CMS error: {str(error)}")


# --- DELETE /meetings/{meeting_number} ---
@meetingRouter.delete("/{meeting_number}", status_code=200)
def delete_meeting(meeting_number: str, session: Session = Depends(get_db), user=Depends(allow_admins_only)):
    user_role = str(getattr(user.role, "value", user.role)).lower().strip()
    try:
        LoggerManager.get_logger().info("User %s deleting meeting number=%s", user.s_id, meeting_number)
        MeetingService(session=session).delete_meeting(number=meeting_number, user_uuid=str(user.UUID), user_role=user_role)
        return {"detail": "Meeting deleted successfully"}
    except HTTPException:
        raise
    except Exception as error:
        LoggerManager.get_logger().exception("Failed to delete meeting number=%s. Error: %s", meeting_number, str(error))
        raise HTTPException(status_code=500, detail="Internal Server Error")

@meetingRouter.put("/name/{meeting_number}", status_code=200, response_model=MeetingOutput)
def update_meeting_name(meeting_number: str, meeting_data: MeetingNameUpdate, access_level: str = None, session: Session = Depends(get_db), user=Depends(validator)):
    user_role = str(getattr(user.role, "value", user.role)).lower().strip()
    try:
        LoggerManager.get_logger().info(
            "User %s:%s (role %s) updating name for meeting number=%s",
            user.s_id, user.UUID, user_role, meeting_number,
        )
        return MeetingService(session=session).update_name_by_number(
            number=meeting_number,
            name=meeting_data.name,
            user_uuid=str(user.UUID),
            user_role=user_role,
            access_level_hint=access_level,
        )
    except HTTPException:
        raise
    except Exception as error:
        LoggerManager.get_logger().exception("Failed to update meeting name number=%s. Error: %s", meeting_number, str(error))
        raise HTTPException(status_code=500, detail="Internal Server Error")


# --- PUT /meetings/password/{meeting_number} ---
@meetingRouter.put("/password/{meeting_number}", status_code=200, response_model=MeetingOutput)
def update_meeting_password(meeting_number: str, meeting_data: MeetingPasswordUpdate, access_level: str = None, session: Session = Depends(get_db), user=Depends(validator)):
    user_role = str(getattr(user.role, "value", user.role)).lower().strip()
    try:
        LoggerManager.get_logger().info(
            "User %s:%s (role %s) updating password for meeting number=%s",
            user.s_id, user.UUID, user_role, meeting_number,
        )
        return MeetingService(session=session).update_password_by_number(
            number=meeting_number,
            password=meeting_data.password,
            user_uuid=str(user.UUID),
            user_role=user_role,
            access_level_hint=access_level,
        )
    except HTTPException:
        raise
    except Exception as error:
        LoggerManager.get_logger().exception("Failed to update password for meeting number=%s. Error: %s", meeting_number, str(error))
        raise HTTPException(status_code=500, detail="Internal Server Error")


# ---------------------------------------------------------------------------
# Participants
# ---------------------------------------------------------------------------
def _authorized_participants(session: Session, meeting_number: str):
    """משתמשים מורשים לפגישה: לפי המדורים המשויכים (group_meeting) וסוג הפגישה."""
    service = MeetingService(session=session)
    cs, cms_type = service._find_cospace(meeting_number)
    if not cs:
        return None  # לא נמצאה ב-CMS
    group_uuids = service._groups_for(meeting_number, cms_type)
    users_seen = set()
    result = []
    for group_uuid in group_uuids:
        group = session.query(Group).filter(Group.UUID == group_uuid).first()
        if not group:
            continue
        for member_access in group.member_access_levels:
            access_val = str(getattr(member_access.access_level, "value", member_access.access_level)).lower()
            if access_val != cms_type:
                continue
            u = session.query(User).filter(User.UUID == member_access.member_uuid).first()
            if u and str(u.UUID) not in users_seen:
                users_seen.add(str(u.UUID))
                result.append({
                    "S_ID": u.s_id,
                    "legId": str(u.UUID),
                    "username": u.username or u.s_id,
                    "role": str(getattr(u.role, "value", u.role)),
                    "group": group.name,
                })
    return result


@meetingRouter.get("/{meeting_number}/participants", status_code=200)
def get_meeting_participants(meeting_number: str, session: Session = Depends(get_db), user=Depends(all_members_validator)):
    participants = _authorized_participants(session, meeting_number)
    if participants is None:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return {"meeting_number": meeting_number, "participants": participants}


@meetingRouter.get("/{meeting_number}/live-participants", status_code=200)
def get_meeting_live_participants(meeting_number: str, session: Session = Depends(get_db), user=Depends(all_members_validator)):
    """משתתפים חיים בשיחה מה-CMS (real leg ids)."""
    service = MeetingService(session=session)
    cs, cms_type = service._find_cospace(meeting_number)
    if not cs:
        raise HTTPException(status_code=404, detail="Meeting not found")
    try:
        cms = CMS(cms_type=cms_type)
        active_calls = cms.get_active_calls()
        active = next((c for c in active_calls if str(c.get("name", "")) == str(meeting_number)), None)
        if not active:
            return {"meeting_number": meeting_number, "call_id": None, "participants": []}
        call_id = active.get("id") or active.get("@id")
        parts = cms.get_call_participants(call_id)
        result = []
        for p in parts:
            leg_id = p.get("legId") or p.get("@id") or p.get("id")
            result.append({
                "name": p.get("name") or p.get("remoteParty") or "—",
                "legId": leg_id,
                "state": p.get("state") or p.get("status") or "connected",
                "mute": str(p.get("audioMuted", p.get("mute", "false"))).lower(),
            })
        return {"meeting_number": meeting_number, "call_id": call_id, "participants": result}
    except Exception as error:
        LoggerManager.get_logger().warning("Failed to fetch live participants for %s: %s", meeting_number, str(error))
        return {"meeting_number": meeting_number, "call_id": None, "participants": []}


@meetingRouter.post("/{meeting_number}/mute", status_code=200)
def mute_meeting_participant(meeting_number: str, body: dict, session: Session = Depends(get_db), user=Depends(allow_admins_only)):
    leg_id = body.get("leg_id")
    call_id = body.get("call_id")
    mute = body.get("mute", True)
    if not leg_id or not call_id:
        raise HTTPException(status_code=400, detail="leg_id and call_id are required")
    _, cms_type = MeetingService(session=session)._find_cospace(meeting_number)
    if not cms_type:
        raise HTTPException(status_code=404, detail="Meeting not found")
    try:
        cms_success = CMS(cms_type=cms_type).mute_participant_by_leg_id(call_id, leg_id, bool(mute))
        return {"success": True, "cms": cms_success}
    except Exception as error:
        LoggerManager.get_logger().warning("CMS mute failed for meeting %s leg %s: %s", meeting_number, leg_id, str(error))
        raise HTTPException(status_code=502, detail=f"CMS error: {str(error)}")


@meetingRouter.post("/{meeting_number}/kick", status_code=200)
def kick_meeting_participant(meeting_number: str, body: dict, session: Session = Depends(get_db), user=Depends(allow_admins_only)):
    leg_id = body.get("leg_id")
    call_id = body.get("call_id")
    if not leg_id or not call_id:
        raise HTTPException(status_code=400, detail="leg_id and call_id are required")
    _, cms_type = MeetingService(session=session)._find_cospace(meeting_number)
    if not cms_type:
        raise HTTPException(status_code=404, detail="Meeting not found")
    try:
        cms_success = CMS(cms_type=cms_type).kick_participant_by_leg_id(call_id, leg_id)
        return {"success": True, "cms": cms_success}
    except Exception as error:
        LoggerManager.get_logger().warning("CMS kick failed for meeting %s leg %s: %s", meeting_number, leg_id, str(error))
        raise HTTPException(status_code=502, detail=f"CMS error: {str(error)}")


# --- GET /meetings/{meeting_number} ---
@meetingRouter.get("/{meeting_number}", status_code=200, response_model=MeetingOutput)
def get_meeting_by_number_single(meeting_number: str, session: Session = Depends(get_db), user=Depends(validator)):
    user_role = getattr(user.role, "value", user.role)
    try:
        return MeetingService(session=session).get_meeting_by_number_for_user(
            number=meeting_number,
            user_uuid=str(user.UUID),
            user_role=user_role,
        )
    except HTTPException:
        raise
    except Exception as error:
        LoggerManager.get_logger().exception("Failed to fetch meeting number=%s. Error: %s", meeting_number, str(error))
        raise HTTPException(status_code=500, detail="Internal Server Error")
