

from typing import Dict

from sqlalchemy import String

from app.models.user import User
from app.repository.groupRepo import GroupRepository
from app.schema.user import (
    GroupInCreate,
    GroupOutput,
    UserInCreateNoRole,

    UserOutput,
    UserInCreate,
    UserInLogin,
    
    
    MemberAccessOutput,
)
from app.models.member_group_access import MemberGroupAccessLevel
from app.security.hashHelper import HashHelp
from app.security.auth import AuthHand
from sqlalchemy.orm import Session
from fastapi import HTTPException
import uuid


class GroupService:
    def __init__(self, session):
        self.__groupRepository = GroupRepository(
            session=session
        )  # מופע הרפוזיטורי
        self.session = session

    def _to_output(self, group) -> GroupOutput:
        """
        ממיר ORM object של מדור ל-Pydantic GroupOutput.
        ×ž×ž×™×¨ ××ª ×”×—×‘×¨×™× ×•×”×¤×’×™×©×•×ª ×œ×¨×©×™×ž×•×ª UUID ×‘×œ×‘×“,
        ×•×’× ×ž×ž×™×¨ ××ª ×¨×ž×•×ª ×”×’×™×©×” ×œ×¤×•×¨×ž×˜ MemberAccessOutput.
        """
        unique_member_ids = list(dict.fromkeys(m.member_uuid for m in group.member_access_levels))

        return GroupOutput(
            UUID=group.UUID,
            name=group.name,
            members=unique_member_ids,
            meetings=group.meeting_numbers,
            member_access_levels=[
                MemberAccessOutput(
                    user_id=row.member_uuid, access_level=row.access_level
                )
                for row in group.member_access_levels
            ],
        )
        
        
    def get_group_members(self, group_uuid: str) -> list[UserOutput]:
        """ מחזיר את כל המשתמשים שיש להם גישה למדור מסוים (דרך member_access_levels) """
        users = self.__groupRepository.get_group_members(group_uuid=group_uuid)
        return users

    def user_is_member_of_group(self, user_uuid: str, group_uuid: str) -> bool:
        """בודק אם משתמש משויך לקבוצה דרך member_group_access."""
        return self.__groupRepository.is_user_member_of_group(
            user_uuid=user_uuid,
            group_uuid=group_uuid,
        )

    def create_group(self, group_data: GroupInCreate) -> GroupOutput:
        return self._to_output(
            self.__groupRepository.create_group(group_data=group_data)
        )

    def get_all_groups(self) -> list[GroupOutput]:
        return [self._to_output(m) for m in self.__groupRepository.get_all_groups()]

    def get_groups_by_user_uuid(self, user_uuid: str) -> list[GroupOutput]:
        """×ž×—×–×™×¨ ×¨×§ ××ª ×”×ž×“×•×¨×™× ×©×œ ×”×ž×©×ª×ž×© ×”×ž×—×•×‘×¨"""
        return [
            self._to_output(m)
            for m in self.__groupRepository.get_groups_by_user_uuid(user_uuid=user_uuid)
        ]

    def get_group_by_uuid(self, group_uuid: str) -> GroupOutput:
        group = self.__groupRepository.get_group_by_uuid(group_uuid=group_uuid)
        if group:
            return self._to_output(group)
        raise HTTPException(status_code=400, detail="Group is not available")

    def delete_group(self, group_uuid: str) -> bool:
        if self.__groupRepository.delete_group(group_uuid=group_uuid):
            return True
        raise HTTPException(status_code=400, detail="Group is not available")

    def update_group(self, group_uuid: str, group_data: GroupInCreate) -> GroupOutput:
        group = self.__groupRepository.update_group(
            group_uuid=group_uuid, group_data=group_data
        )
        if group:
            return self._to_output(group)
        raise HTTPException(status_code=400, detail="Group is not available")

    # היררכיית roles: super_admin > admin > agent > viewer
    ROLE_HIERARCHY = {"super_admin": 4, "admin": 3, "agent": 2}

    def add_member_to_group(
        self,
        group_uuid: str,
        user_s_id: str,
        access_level: MemberGroupAccessLevel,
        requester_uuid: str = None,
        requester_role: str = None,
    ) -> GroupOutput:
        """
        מוסיף חבר למדור עם רמת גישה.
        היררכיית הרשאות:
        - super_admin: יכול לשייך את כולם חוץ מעצמו
        - admin: יכול לשייך agent ו-viewer בלבד
        - agent: יכול לשייך רק viewer, ורק לקבוצות שהוא שייך אליהן
        - viewer: לא יכול לשייך אף אחד
        """
        requester_level = self.ROLE_HIERARCHY.get(requester_role, 0)

        # viewer לא יכול לשייך אף אחד
        if requester_level < 2:
            raise HTTPException(status_code=403, detail="Insufficient permissions to add members to groups")

        # שולף את המשתמש המוסף
        target = self.__groupRepository._find_user(user_s_id)
        if not target:
            raise HTTPException(status_code=400, detail="User not found")

        target_role = getattr(target.role, "value", str(target.role))
        target_level = self.ROLE_HIERARCHY.get(target_role, 0)

        # לא ניתן לשייך את עצמך
        if str(target.UUID) == str(requester_uuid):
            raise HTTPException(status_code=403, detail="You cannot add yourself to a group")

        # לא ניתן לשייך מישהו עם role גבוה או שווה לשלך
        if target_level >= requester_level:
            raise HTTPException(
                status_code=403,
                detail=f"{requester_role.capitalize()} cannot add a user with role '{target_role}'"
            )

        # agent חייב להיות חבר בקבוצה
        if requester_role == "agent":
            if not self.__groupRepository.is_user_member_of_group(requester_uuid, group_uuid):
                raise HTTPException(status_code=403, detail="Agent can only manage groups they belong to")

        group = self.__groupRepository.add_member_to_group(
            group_uuid=group_uuid,
            user_s_id=user_s_id,
            access_level=access_level,
        )
        if group:
            return self._to_output(group)
        raise HTTPException(status_code=400, detail="Group or User is not available")

    def remove_member_from_group(self, group_uuid: str, user_s_id: str) -> GroupOutput:
        group = self.__groupRepository.remove_member_from_group(
            group_uuid=group_uuid, user_s_id=user_s_id
        )
        if group:
            return self._to_output(group)
        raise HTTPException(status_code=400, detail="Group or User is not available")

    def remove_member_access_from_group(
        self,
        group_uuid: str,
        user_s_id: str,
        access_level: MemberGroupAccessLevel,
        requester_uuid: str = None,
        requester_role: str = None,
    ) -> GroupOutput:
        requester_level = self.ROLE_HIERARCHY.get(requester_role, 0)
        if requester_level < 2:
            raise HTTPException(status_code=403, detail="Insufficient permissions to remove members from groups")

        target = self.__groupRepository._find_user(user_s_id)
        if not target:
            raise HTTPException(status_code=400, detail="User not found")

        target_role = getattr(target.role, "value", str(target.role))
        target_level = self.ROLE_HIERARCHY.get(target_role, 0)

        if str(target.UUID) == str(requester_uuid):
            raise HTTPException(status_code=403, detail="You cannot remove yourself from a group")

        if target_level >= requester_level:
            raise HTTPException(
                status_code=403,
                detail=f"{requester_role.capitalize()} cannot remove a user with role '{target_role}'",
            )

        if requester_role == "agent":
            if not self.__groupRepository.is_user_member_of_group(requester_uuid, group_uuid):
                raise HTTPException(status_code=403, detail="Agent can only manage groups they belong to")

        if requester_role == "admin":
            requester = self.__groupRepository._find_user(requester_uuid)
            av = str(getattr(access_level, "value", access_level)).lower()
            if av == "audio" and not getattr(requester, "can_audio", False):
                raise HTTPException(status_code=403, detail="Admin not authorized for audio access")
            if av == "video" and not getattr(requester, "can_video", False):
                raise HTTPException(status_code=403, detail="Admin not authorized for video access")

        group = self.__groupRepository.remove_member_access_from_group(
            group_uuid=group_uuid,
            user_s_id=user_s_id,
            access_level=access_level,
        )
        if group:
            return self._to_output(group)
        raise HTTPException(status_code=400, detail="Group or User is not available")

    def add_meeting_to_group(self, group_uuid: str, meeting_number: str, requester_uuid: str = None, requester_role: str = None, access_level_hint: str = None) -> GroupOutput:
        # סוג הפגישה נקבע לפי ה-CMS (audio/video) — גם מאמת שהפגישה קיימת
        # Handle composite ID format: "number:access_level"
        from app.service.meetingService import MeetingService
        actual_meeting_number = meeting_number.split(":")[0] if ":" in meeting_number else meeting_number
        meeting_service = MeetingService(session=self.session)
        # If access_level_hint is provided, use it directly to avoid wrong CMS type detection
        if access_level_hint and access_level_hint.lower() in ("audio", "video"):
            meeting_type = access_level_hint.lower()
            cs = meeting_service._find_cospace_by_type(actual_meeting_number, meeting_type)
            if not cs:
                raise HTTPException(status_code=404, detail="Meeting not found in CMS")
        else:
            cs, meeting_type = meeting_service._find_cospace(actual_meeting_number)
            if not cs or not meeting_type:
                raise HTTPException(status_code=404, detail="Meeting not found in CMS")

        if requester_role == "admin" and requester_uuid:
            requester = self.__groupRepository._find_user(requester_uuid)
            if meeting_type == "audio" and not getattr(requester, "can_audio", False):
                raise HTTPException(status_code=403, detail="Admin not authorized for audio meetings")
            if meeting_type == "video" and not getattr(requester, "can_video", False):
                raise HTTPException(status_code=403, detail="Admin not authorized for video meetings")

        meeting_service._ensure_meeting_exists(actual_meeting_number, meeting_type)
        group = self.__groupRepository.add_meeting_to_group_by_number(
            group_uuid=group_uuid, meeting_number=actual_meeting_number, access_level=meeting_type,
        )
        if group:
            return self._to_output(group)
        raise HTTPException(status_code=400, detail="Group or Meeting is not available")

    def remove_meeting_from_group(self, group_uuid: str, meeting_number: str, access_level_hint: str = None) -> GroupOutput:
        from app.service.meetingService import MeetingService
        actual_meeting_number = meeting_number.split(":")[0] if ":" in meeting_number else meeting_number
        if access_level_hint and access_level_hint.lower() in ("audio", "video"):
            meeting_type = access_level_hint.lower()
        else:
            _, meeting_type = MeetingService(session=self.session)._find_cospace(actual_meeting_number)
        group = self.__groupRepository.remove_meeting_from_group_by_number(
            group_uuid=group_uuid, meeting_number=actual_meeting_number, access_level=meeting_type,
        )
        if group:
            return self._to_output(group)
        raise HTTPException(status_code=400, detail="Group or Meeting is not available")
