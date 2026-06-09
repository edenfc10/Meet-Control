from app.models.meeting import AccessLevel
from app.models.server import Server
from app.repository.base import BaseRepository
from app.schema.server import ServerInCreate, ServerInUpdate


class ServerRepository(BaseRepository):
    def create_server(self, server_data: ServerInCreate) -> Server:
        new_server = Server(**server_data.model_dump())
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

    def update_server(self, server_uuid: str, server_data: ServerInUpdate) -> Server | None:
        server = self.get_server_by_uuid(server_uuid=server_uuid)
        if not server:
            return None

        for key, value in server_data.model_dump(exclude_none=True).items():
            setattr(server, key, value)

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
