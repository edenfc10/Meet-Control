from typing import Optional
from uuid import UUID
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from app.models.meeting import AccessLevel


class ConnectionStatus(str, Enum):
    """סטטוסי חיבור שרת"""
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    TESTING = "testing"
    PENDING = "pending"


class ServerInCreate(BaseModel):
    server_name: str = Field(min_length=1, max_length=120)
    ip_address: str = Field(min_length=1, max_length=45)
    port: int = Field(default=8443, ge=1, le=65535, description="פורט השרת")
    username: str = Field(min_length=1, max_length=120)
    password: str = Field(min_length=1, max_length=255)
    accessLevel: AccessLevel
    is_primary: bool = Field(default=False, description="האם זה השרת הראשי")

    model_config = ConfigDict(extra="forbid")


class ServerInUpdate(BaseModel):
    server_name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    ip_address: Optional[str] = Field(default=None, min_length=1, max_length=45)
    port: Optional[int] = Field(default=None, ge=1, le=65535, description="פורט השרת")
    username: Optional[str] = Field(default=None, min_length=1, max_length=120)
    password: Optional[str] = Field(default=None, min_length=1, max_length=255)
    accessLevel: Optional[AccessLevel] = None
    is_active: Optional[bool] = Field(default=None, description="האם השרת פעיל")
    is_primary: Optional[bool] = Field(default=None, description="האם זה השרת הראשי")
    hierarchy_order: Optional[int] = Field(default=None, ge=0, description="סדר היררכיה")

    model_config = ConfigDict(extra="forbid")


class ServerOutput(BaseModel):
    UUID: UUID
    server_name: str
    ip_address: str
    port: int
    username: str
    password: str
    accessLevel: AccessLevel
    is_active: bool
    is_primary: bool
    hierarchy_order: int
    connection_status: ConnectionStatus
    last_connection_test: Optional[datetime] = None
    connection_error: Optional[str] = None
    server_version: Optional[str] = None
    system_info: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ConnectionTestResult(BaseModel):
    """תוצאת בדיקת חיבור"""
    success: bool
    message: str
    server_version: Optional[str] = None
    system_info: Optional[str] = None
    response_time_ms: Optional[float] = None


class ServerSetPrimary(BaseModel):
    """מודל להגדרת שרת ראשי"""
    server_uuid: UUID = Field(..., description="מזהה השרת להגדרה כראשי")


class ServerStats(BaseModel):
    """סטטיסטיקת שרתים"""
    total: int
    connected: int
    disconnected: int
    error: int


