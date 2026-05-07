from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.meeting import AccessLevel
from app.schema.server import (
    ServerInCreate, ServerInUpdate, ServerOutput, 
    ConnectionTestResult, ServerSetPrimary, ServerStats
)
from app.security.TokenValidator import TokenValidator
from app.service.serverService import ServerService
from logger import LoggerManager

serverRouter = APIRouter()

allow_super_admin_only = TokenValidator(allowed_roles=["super_admin"])
allow_admins_only = TokenValidator(allowed_roles=["admin", "super_admin"])

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
            "User %s:%s with role %s is creating a server",
            user.s_id,
            user.UUID,
            user.role.value,
        )
        LoggerManager.get_logger().info(f"Received server data: {server_data}")
        LoggerManager.get_logger().info(f"Server data type: {type(server_data)}")
        LoggerManager.get_logger().info(f"AccessLevel value: {server_data.accessLevel}")
        LoggerManager.get_logger().info(f"AccessLevel type: {type(server_data.accessLevel)}")
        
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


# --- CMS Server Management Endpoints ---

@serverRouter.get("/active", status_code=200, response_model=list[ServerOutput])
def get_active_servers(
    session: Session = Depends(get_db),
    user=Depends(allow_admins_only),
):
    """קבלת רשימת שרתים פעילים ומחוברים בלבד"""
    try:
        LoggerManager.get_logger().info(
            "User %s:%s requested active CMS servers",
            user.s_id, user.UUID
        )
        return ServerService(session=session).get_active_servers()
    except Exception as error:
        LoggerManager.get_logger().exception(
            "Failed to get active servers for user %s:%s. Error: %s",
            user.s_id, user.UUID, str(error)
        )
        raise HTTPException(status_code=500, detail="Internal Server Error")


@serverRouter.get("/primary", status_code=200, response_model=ServerOutput)
def get_primary_server(
    session: Session = Depends(get_db),
    user=Depends(allow_admins_only),
):
    """קבלת השרת הראשי"""
    try:
        LoggerManager.get_logger().info(
            "User %s:%s requested primary CMS server",
            user.s_id, user.UUID
        )
        primary_server = ServerService(session=session).get_primary_server()
        if not primary_server:
            raise HTTPException(status_code=404, detail="לא הוגדר שרת ראשי")
        return primary_server
    except HTTPException:
        raise
    except Exception as error:
        LoggerManager.get_logger().exception(
            "Failed to get primary server for user %s:%s. Error: %s",
            user.s_id, user.UUID, str(error)
        )
        raise HTTPException(status_code=500, detail="Internal Server Error")


@serverRouter.post("/{server_uuid}/test-connection", status_code=200, response_model=ConnectionTestResult)
def test_server_connection(
    server_uuid: str = Path(..., description="UUID של השרת"),
    session: Session = Depends(get_db),
    user=Depends(allow_admins_only),
):
    """בדיקת חיבור לשרת CMS ספציפי"""
    try:
        LoggerManager.get_logger().info(
            "User %s:%s testing connection to server %s",
            user.s_id, user.UUID, server_uuid
        )
        return ServerService(session=session).test_connection(server_uuid=server_uuid)
    except HTTPException:
        raise
    except Exception as error:
        LoggerManager.get_logger().exception(
            "Failed to test connection for server %s. Error: %s",
            server_uuid, str(error)
        )
        raise HTTPException(status_code=500, detail="Internal Server Error")


@serverRouter.post("/set-primary", status_code=200)
def set_primary_server(
    request: ServerSetPrimary,
    session: Session = Depends(get_db),
    user=Depends(allow_super_admin_only),
):
    """הגדרת שרת כראשי"""
    try:
        LoggerManager.get_logger().info(
            "User %s:%s setting server %s as primary",
            user.s_id, user.UUID, str(request.server_uuid)
        )
        success = ServerService(session=session).set_primary_server(str(request.server_uuid))
        if success:
            return {"detail": "שרת הוגדר כראשי בהצלחה"}
        else:
            raise HTTPException(status_code=400, detail="לא ניתן היה להגדיר את השרת כראשי")
    except HTTPException:
        raise
    except Exception as error:
        LoggerManager.get_logger().exception(
            "Failed to set primary server %s. Error: %s",
            str(request.server_uuid), str(error)
        )
        raise HTTPException(status_code=500, detail="Internal Server Error")


@serverRouter.get("/stats", status_code=200, response_model=ServerStats)
def get_server_stats(
    session: Session = Depends(get_db),
    user=Depends(allow_admins_only),
):
    """קבלת סטטיסטיקת שרתים"""
    try:
        LoggerManager.get_logger().info(
            "User %s:%s requested server statistics",
            user.s_id, user.UUID
        )
        return ServerService(session=session).get_server_stats()
    except Exception as error:
        LoggerManager.get_logger().exception(
            "Failed to get server stats for user %s:%s. Error: %s",
            user.s_id, user.UUID, str(error)
        )
        raise HTTPException(status_code=500, detail="Internal Server Error")
