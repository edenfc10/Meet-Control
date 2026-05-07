from typing import Dict, Any
from datetime import datetime
from app.models.meeting import AccessLevel
from app.models.server import Server
from app.repository.base import BaseRepository
from app.schema.server import ServerInCreate, ServerInUpdate


class ServerRepository(BaseRepository):
    def create_server(self, server_data: Dict[str, Any]) -> Server:
        """יצירת שרת חדש עם תמיכה בסטטוס CMS"""
        new_server = Server(**server_data)
        self.session.add(new_server)
        self.session.commit()
        self.session.refresh(new_server)
        return new_server

    def get_all_servers(self, access_level: AccessLevel | None = None) -> list[Server]:
        query = self.session.query(Server)
        if access_level is not None:
            query = query.filter(Server.accessLevel == access_level)
        return query.order_by(Server.created_at.desc(), Server.server_name.asc()).all()

    def get_server_by_uuid(self, server_uuid: str) -> Server | None:
        return self.session.query(Server).filter(Server.UUID == server_uuid).first()

    def get_server_by_id(self, server_id: int) -> Server | None:
        return self.session.query(Server).filter(Server.id == server_id).first()

    def update_server(self, server_uuid: str, server_data: Dict[str, Any]) -> Server | None:
        server = self.get_server_by_uuid(server_uuid=server_uuid)
        if not server:
            return None

        for key, value in server_data.items():
            setattr(server, key, value)

        server.updated_at = datetime.utcnow()
        self.session.commit()
        self.session.refresh(server)
        return server

    def delete_server(self, server_uuid: str) -> bool:
        server = self.get_server_by_uuid(server_uuid=server_uuid)
        if not server:
            return False

        self.session.delete(server)
        self.session.commit()
        return True

    def update_connection_status(self, server_uuid: str, status: str, error: str = None, 
                               version: str = None, system_info: str = None, 
                               last_test: datetime = None) -> bool:
        """עדכון סטטוס חיבור"""
        server = self.get_server_by_uuid(server_uuid=server_uuid)
        if not server:
            return False

        server.connection_status = status
        server.last_connection_test = last_test or datetime.utcnow()
        server.connection_error = error
        server.server_version = version
        server.system_info = system_info
        server.updated_at = datetime.utcnow()
        self.session.commit()
        return True

    def set_primary_server(self, server_uuid: str) -> bool:
        """הגדרת שרת כראשי (מבטל את כל האחרים)"""
        server = self.get_server_by_uuid(server_uuid=server_uuid)
        if not server:
            return False
        
        # ביטול כל השרתים הראשיים הקיימים
        old_primary_servers = self.session.query(Server).filter(Server.is_primary == True).all()
        for old_server in old_primary_servers:
            old_server.is_primary = False
        
        # הגדרת השרת החדש כראשי
        server.is_primary = True
        server.updated_at = datetime.utcnow()
        self.session.commit()
        return True
