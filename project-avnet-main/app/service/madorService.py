
from typing import Dict

from sqlalchemy import String

from app.models.user import User
from app.repository.madorRepo import MadorRepository
from app.schema.user import MadorInCreate, MadorOutput, UserInCreateNoRole, UserJWTData, UserOutput, UserInCreate, UserInLogin, UserToken, UserWithToken
from app.security.hashHelper import HashHelp
from app.security.auth import AuthHand
from sqlalchemy.orm import Session
from fastapi import HTTPException
import uuid

# ניהול לוגיקה של הרשמה והתחברות של משתמשים
class MadorService:
    def __init__(self, session):
        self.__madorRepository = MadorRepository(session=session)
        self.session = session

    def _to_output(self, mador) -> MadorOutput:
        return MadorOutput(
            UUID=mador.UUID,
            name=mador.name,
            members=[m.UUID for m in mador.members],
            meetings=[m.UUID for m in mador.meetings],
        )

    def create_mador(self, mador_data: MadorInCreate) -> MadorOutput:
        return self._to_output(self.__madorRepository.create_mador(mador_data=mador_data))
    
    def get_all_madors(self) -> list[MadorOutput]:
        return [self._to_output(m) for m in self.__madorRepository.get_all_madors()]
    
    def get_mador_by_uuid(self, mador_uuid: str) -> MadorOutput:
        mador = self.__madorRepository.get_mador_by_uuid(mador_uuid=mador_uuid)
        if mador:
            return self._to_output(mador)
        raise HTTPException(status_code=400, detail="Mador is not available")

    def delete_mador(self, mador_uuid: str) -> bool:
        if self.__madorRepository.delete_mador(mador_uuid=mador_uuid):
            return True
        raise HTTPException(status_code=400, detail="Mador is not available")
    
    def update_mador(self, mador_uuid: str, mador_data: MadorInCreate) -> MadorOutput:
        mador = self.__madorRepository.update_mador(mador_uuid=mador_uuid, mador_data=mador_data)
        if mador:
            return self._to_output(mador)
        raise HTTPException(status_code=400, detail="Mador is not available")

    def add_member_to_mador(self, mador_uuid: str, user_s_id: str) -> MadorOutput:
        mador = self.__madorRepository.add_member_to_mador(mador_uuid=mador_uuid, user_s_id=user_s_id)
        if mador:
            return self._to_output(mador)
        raise HTTPException(status_code=400, detail="Mador or User is not available")
    
    def remove_member_from_mador(self, mador_uuid: str, user_s_id: str) -> MadorOutput:
        mador = self.__madorRepository.remove_member_from_mador(mador_uuid=mador_uuid, user_s_id=user_s_id)
        if mador:
            return self._to_output(mador)
        raise HTTPException(status_code=400, detail="Mador or User is not available")

    def add_meeting_to_mador(self, mador_uuid: str, meeting_uuid: str) -> MadorOutput:
        mador = self.__madorRepository.add_meeting_to_mador_by_uuid(mador_uuid=mador_uuid, meeting_uuid=meeting_uuid)
        if mador:
            return self._to_output(mador)
        raise HTTPException(status_code=400, detail="Mador or Meeting is not available")