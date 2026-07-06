from fastapi import HTTPException
from app.models.meeting import AccessLevel
from app.repository.severRepo import ServerRepository
from app.schema.server import ServerInCreate, ServerInUpdate, ServerOutput
from app.service.cms import CMS


class ServerService:
    def __init__(self, session):
        self.__serverRepository = ServerRepository(session=session)

    def _to_output(self, server) -> ServerOutput:
        return ServerOutput.model_validate(server)

    def _check_and_set_active(self, ip_address: str, port: int, username: str, password: str, require_connection: bool = True) -> bool:
        """בודק חיבור ל-CMS. אם require_connection=True וחיבור נכשל — זורק 502."""
        is_active = CMS.check_connection(ip_address, port, username, password)
        if require_connection and not is_active:
            raise HTTPException(
                status_code=502,
                detail=(
                    f"Failed to connect to CMS at {ip_address}:{port}. "
                    "The server is unreachable, the credentials are incorrect, or the access level does not match this server. "
                    "Please verify and try again."
                ),
            )
        return is_active

    def create_server(self, server_data: ServerInCreate) -> ServerOutput:
        is_active = self._check_and_set_active(
            server_data.ip_address, server_data.port, server_data.username, server_data.password
        )
        return self._to_output(self.__serverRepository.create_server(server_data=server_data, is_active=is_active))

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
        existing = self.__serverRepository.get_server_by_uuid(server_uuid=server_uuid)
        if not existing:
            raise HTTPException(status_code=404, detail="Server not found")
        new_ip = server_data.ip_address or existing.ip_address
        new_port = server_data.port or existing.port
        new_user = server_data.username or existing.username
        new_pass = server_data.password or existing.password
        is_active = self._check_and_set_active(new_ip, new_port, new_user, new_pass)
        updated_server = self.__serverRepository.update_server(server_uuid=server_uuid, server_data=server_data, is_active=is_active)
        if updated_server:
            return self._to_output(updated_server)
        raise HTTPException(status_code=404, detail="Server not found")