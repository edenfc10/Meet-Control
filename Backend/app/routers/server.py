from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.meeting import AccessLevel
from app.schema.server import ServerInCreate, ServerInUpdate, ServerOutput
from app.security.TokenValidator import TokenValidator
from app.service.serverService import ServerService
from logger import LoggerManager

serverRouter = APIRouter()

allow_super_admin_only = TokenValidator(allowed_roles=["super_admin"])

@serverRouter.get("/all", status_code=200, response_model=list[ServerOutput])
def get_all_servers(
    session: Session = Depends(get_db),
    access_level: Optional[AccessLevel] = None,
    user=Depends(allow_super_admin_only),
):
    try:
        LoggerManager.get_logger().info(
            "User %s:%s with role %s requested all servers with access level=%s",
            user.s_id,
            user.UUID,
            user.role.value,
            access_level,
        )
        return ServerService(session=session).get_all_servers(access_level=access_level)
    except Exception as error:
        LoggerManager.get_logger().exception(
            "Failed to fetch servers for user %s:%s role=%s. Error: %s",
            user.s_id,
            user.UUID,
            user.role.value,
            str(error),
        )
        raise HTTPException(status_code=500, detail="Internal Server Error")


@serverRouter.post("/", status_code=201, response_model=ServerOutput)
def create_server(
    server_data: ServerInCreate,
    session: Session = Depends(get_db),
    user=Depends(allow_super_admin_only),
):
    try:
        LoggerManager.get_logger().info(
            "User %s:%s with role %s is creating a server for access level %s",
            user.s_id,
            user.UUID,
            user.role.value,
            server_data.accessLevel,
        )
        return ServerService(session=session).create_server(server_data=server_data)
    except Exception as error:
        LoggerManager.get_logger().exception(
            "Failed to create server for user %s:%s role=%s. Error: %s",
            user.s_id,
            user.UUID,
            user.role.value,
            str(error),
        )
        raise HTTPException(status_code=500, detail="Internal Server Error")


@serverRouter.put("/{server_uuid}", status_code=200, response_model=ServerOutput)
def update_server(
    server_uuid: str,
    server_data: ServerInUpdate,
    session: Session = Depends(get_db),
    user=Depends(allow_super_admin_only),
):
    try:
        LoggerManager.get_logger().info(
            "User %s:%s with role %s requested to update server with UUID=%s",
            user.s_id,
            user.UUID,
            user.role.value,
            server_uuid,
        )
        return ServerService(session=session).update_server(server_uuid=server_uuid, server_data=server_data)
    except HTTPException:
        raise
    except Exception as error:
        LoggerManager.get_logger().exception(
            "Failed to update server with UUID=%s. Error: %s", server_uuid, str(error),
        )
        raise HTTPException(status_code=500, detail="Internal Server Error")


@serverRouter.delete("/{server_uuid}", status_code=200)
def delete_server(
    server_uuid: str,
    session: Session = Depends(get_db),
    user=Depends(allow_super_admin_only),
):
    try:
        LoggerManager.get_logger().info(
            "User %s:%s with role %s requested to delete server with UUID=%s",
            user.s_id,
            user.UUID,
            user.role.value,
            server_uuid,
        )
        ServerService(session=session).delete_server(server_uuid=server_uuid)
        return {"detail": "Server deleted successfully"}
    except HTTPException:
        raise
    except Exception as error:
        LoggerManager.get_logger().exception(
            "Failed to delete server with UUID=%s. Error: %s",
            server_uuid,
            str(error),
        )
        raise HTTPException(status_code=500, detail="Internal Server Error")
