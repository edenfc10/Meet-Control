from fastapi import HTTPException
from app.models.meeting import AccessLevel
from app.repository.severRepo import ServerRepository
from app.schema.server import ServerInCreate, ServerInUpdate, ServerOutput

class ServerService:
    def __init__(self, session):
        self.__serverRepository = ServerRepository(session=session)

    def _to_output(self, server) -> ServerOutput:
        return ServerOutput.model_validate(server)

    def create_server(self, server_data: ServerInCreate) -> ServerOutput:
        return self._to_output(self.__serverRepository.create_server(server_data=server_data))

    def get_all_servers(self, access_level: AccessLevel | None = None) -> list[ServerOutput]:
        return [
            self._to_output(server)
            for server in self.__serverRepository.get_all_servers(access_level=access_level)
        ]

    def delete_server(self, server_uuid: str) -> None:
        success = self.__serverRepository.delete_server(server_uuid=server_uuid)
        if not success:
            raise HTTPException(status_code=404, detail="Server not found")

    def update_server(self, server_uuid: str, server_data: ServerInUpdate) -> ServerOutput:
        updated_server = self.__serverRepository.update_server(server_uuid=server_uuid, server_data=server_data)
        if updated_server:
            return self._to_output(updated_server)
        raise HTTPException(status_code=404, detail="Server not found")