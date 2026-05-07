from typing import Optional, List
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.models.meeting import AccessLevel
from app.models.server import Server
from app.repository.severRepo import ServerRepository
from app.schema.server import (
    ServerInCreate, ServerInUpdate, ServerOutput, 
    ConnectionTestResult, ServerSetPrimary, ServerStats
)
from app.service.cms import CMS
from datetime import datetime
import time
import threading
from logger import LoggerManager

class ServerService:
    def __init__(self, session: Session):
        self.__serverRepository = ServerRepository(session=session)
        self.logger = LoggerManager.get_logger()

    def _to_output(self, server: Server) -> ServerOutput:
        """המרת מודל Server ל-Pydantic output"""
        try:
            self.logger.info(f"Converting server to output - UUID: {server.UUID}, name: {server.server_name}")
            self.logger.info(f"Server fields - accessLevel: {server.accessLevel}, connection_status: {server.connection_status}")
            
            # Handle connection_status conversion
            connection_status = server.connection_status
            if isinstance(connection_status, str):
                from app.schema.server import ConnectionStatus
                try:
                    connection_status = ConnectionStatus(connection_status)
                except ValueError:
                    self.logger.warning(f"Invalid connection_status value: {connection_status}, defaulting to 'disconnected'")
                    connection_status = ConnectionStatus.DISCONNECTED
            
            output = ServerOutput(
                UUID=server.UUID,
                server_name=server.server_name,
                ip_address=server.ip_address,
                port=server.port,
                username=server.username,
                password=server.password,
                accessLevel=server.accessLevel,
                is_active=server.is_active,
                is_primary=server.is_primary,
                hierarchy_order=server.hierarchy_order,
                connection_status=connection_status,
                last_connection_test=server.last_connection_test,
                connection_error=server.connection_error,
                server_version=server.server_version,
                system_info=server.system_info,
                created_at=server.created_at,
                updated_at=server.updated_at
            )
            
            self.logger.info(f"Successfully converted server {server.server_name} to output")
            return output
            
        except Exception as e:
            self.logger.error(f"Error in _to_output for server {server.server_name}: {str(e)}")
            self.logger.error(f"Server data: UUID={server.UUID}, name={server.server_name}, accessLevel={server.accessLevel}")
            raise

    def create_server(self, server_data: ServerInCreate) -> ServerOutput:
        """יצירת שרת CMS חדש - הוספה ל-DB ואז בדיקת חיבור אסינכרונית"""
        try:
            self.logger.info(f"Starting server creation for: {server_data.server_name}")
            
            # בדיקה אם כבר יש שרת ראשי אם מנסים להגדיר חדש
            if server_data.is_primary:
                self.logger.info("Checking for existing primary server...")
                existing_primary = self.get_primary_server()
                if existing_primary:
                    self.logger.warning(f"Primary server already exists: {existing_primary.server_name}")
                    raise HTTPException(
                        status_code=400, 
                        detail="כבר קיים שרת ראשי. יש לבטל את השרת הראשי הקיים קודם."
                    )
            
            # יצירת השרת ב-DB עם סטטוס pending
            self.logger.info("Creating server in database with pending status...")
            server_dict = server_data.dict()
            server_dict['connection_status'] = 'pending'
            server_dict['last_connection_test'] = None
            server_dict['connection_error'] = None
            server_dict['server_version'] = None
            server_dict['system_info'] = None
            
            self.logger.info(f"Server data for DB: {server_dict}")
            
            try:
                server = self.__serverRepository.create_server(server_data=server_dict)
                self.logger.info(f"Server created in DB with UUID: {server.UUID}")
            except Exception as db_error:
                self.logger.error(f"Database creation failed: {str(db_error)}")
                raise HTTPException(status_code=500, detail="שגיאה ביצירת שרת במסד הנתונים")
            
            # הפעלת בדיקת חיבור ברקע (אסינכרונית)
            self.logger.info("Starting background connection test...")
            self._test_connection_async(server.UUID)
            
            try:
                self.logger.info("Converting server to output format...")
                output = self._to_output(server)
                self.logger.info("Server creation completed successfully")
                return output
            except Exception as output_error:
                self.logger.error(f"Output conversion failed: {str(output_error)}")
                raise HTTPException(status_code=500, detail="שגיאה בהמרת נתוני שרת")
            
        except HTTPException:
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error in create_server: {str(e)}")
            raise HTTPException(status_code=500, detail="שגיאה ביצירת שרת CMS")

    def get_all_servers(self, access_level: AccessLevel | None = None) -> list[ServerOutput]:
        """קבלת כל השרתים"""
        try:
            servers = self.__serverRepository.get_all_servers(access_level=access_level)
            self.logger.info(f"Found {len(servers)} servers in database")
            
            result = []
            for i, server in enumerate(servers):
                try:
                    self.logger.info(f"Processing server {i+1}: {server.server_name}, access_level: {server.accessLevel}")
                    output = self._to_output(server)
                    result.append(output)
                except Exception as e:
                    self.logger.error(f"Error converting server {server.server_name} to output: {str(e)}")
                    raise
            return result
        except Exception as e:
            self.logger.error(f"Error in get_all_servers: {str(e)}")
            raise

    def get_active_servers(self) -> List[ServerOutput]:
        """קבלת שרתים פעילים ומחוברים בלבד"""
        servers = self.__serverRepository.get_all_servers()
        return [
            self._to_output(server) 
            for server in servers 
            if server.is_active and server.connection_status == 'connected'
        ]

    def get_primary_server(self) -> Optional[ServerOutput]:
        """קבלת השרת הראשי"""
        servers = self.__serverRepository.get_all_servers()
        primary_server = next((s for s in servers if s.is_primary), None)
        return self._to_output(primary_server) if primary_server else None

    def delete_server(self, server_uuid: str) -> None:
        """מחיקת שרת (soft delete)"""
        try:
            server = self.__serverRepository.get_server_by_uuid(server_uuid)
            if not server:
                raise HTTPException(status_code=404, detail="Server not found")
            
            success = self.__serverRepository.delete_server(server_uuid=server_uuid)
            if success:
                self.logger.info("CMS server deleted: %s", server.server_name)
            
        except HTTPException:
            raise
        except Exception as e:
            self.logger.error("Failed to delete CMS server %s: %s", server_uuid, str(e))
            raise HTTPException(status_code=500, detail="שגיאה במחיקת שרת CMS")

    def update_server(self, server_uuid: str, server_data: ServerInUpdate) -> ServerOutput:
        """עדכון שרת CMS"""
        try:
            server = self.__serverRepository.get_server_by_uuid(server_uuid)
            if not server:
                raise HTTPException(status_code=404, detail="Server not found")
            
            update_dict = server_data.dict(exclude_unset=True)
            
            # אם מעדכנים פרטי התחברות - בדוק חיבור מחדש
            if any(key in update_dict for key in ['ip_address', 'port', 'username', 'password']):
                host = update_dict.get('ip_address', server.ip_address)
                port = update_dict.get('port', server.port)
                username = update_dict.get('username', server.username)
                password = update_dict.get('password', server.password)
                
                connection_result = self._test_connection_direct(host, port, username, password)
                
                if not connection_result.success:
                    raise HTTPException(
                        status_code=400,
                        detail=f"בדיקת חיבור נכשלה: {connection_result.message}"
                    )
                
                update_dict.update({
                    'connection_status': 'connected',
                    'server_version': connection_result.server_version,
                    'system_info': connection_result.system_info,
                    'last_connection_test': datetime.utcnow(),
                    'connection_error': None
                })
            
            # אם מגדירים כראשי
            if update_dict.get('is_primary') == True:
                self.set_primary_server(server_uuid)
                update_dict.pop('is_primary')  # כבר טופל
            
            updated_server = self.__serverRepository.update_server(server_uuid=server_uuid, server_data=update_dict)
            
            if updated_server:
                self.logger.info("CMS server updated: %s", updated_server.server_name)
                return self._to_output(updated_server)
            
            raise HTTPException(status_code=404, detail="Server not found")
            
        except HTTPException:
            raise
        except Exception as e:
            self.logger.error("Failed to update CMS server %s: %s", server_uuid, str(e))
            raise HTTPException(status_code=500, detail="שגיאה בעדכון שרת CMS")

    def test_connection(self, server_uuid: str) -> ConnectionTestResult:
        """בדיקת חיבור לשרת קיים"""
        try:
            server = self.__serverRepository.get_server_by_uuid(server_uuid)
            if not server:
                raise HTTPException(status_code=404, detail="Server not found")
            
            result = self._test_connection_direct(
                server.ip_address, server.port, server.username, server.password
            )
            
            # עדכון סטטוס במסד נתונים
            status = 'connected' if result.success else 'error'
            error = None if result.success else result.message
            
            self.__serverRepository.update_connection_status(server_uuid, status, error)
            
            return result
            
        except HTTPException:
            raise
        except Exception as e:
            self.logger.error("Failed to test connection for server %s: %s", server_uuid, str(e))
            raise HTTPException(status_code=500, detail="שגיאה בבדיקת חיבור")

    def set_primary_server(self, server_uuid: str) -> bool:
        """הגדרת שרת כראשי"""
        try:
            server = self.__serverRepository.get_server_by_uuid(server_uuid)
            if not server:
                raise HTTPException(status_code=404, detail="Server not found")
            
            if server.connection_status != 'connected':
                raise HTTPException(
                    status_code=400, 
                    detail="ניתן להגדיר כראשי רק שרת מחובר"
                )
            
            success = self.__serverRepository.set_primary_server(server_uuid)
            
            if success:
                self.logger.info("CMS server set as primary: %s", server.server_name)
            
            return success
            
        except HTTPException:
            raise
        except Exception as e:
            self.logger.error("Failed to set primary server %s: %s", server_uuid, str(e))
            raise HTTPException(status_code=500, detail="שגיאה בהגדרת שרת ראשי")

    def get_server_stats(self) -> ServerStats:
        """קבלת סטטיסטיקת שרתים"""
        servers = self.__serverRepository.get_all_servers()
        
        total = len([s for s in servers if s.is_active])
        connected = len([s for s in servers if s.is_active and s.connection_status == 'connected'])
        disconnected = len([s for s in servers if s.is_active and s.connection_status == 'disconnected'])
        error = len([s for s in servers if s.is_active and s.connection_status == 'error'])
        
        return ServerStats(
            total=total,
            connected=connected,
            disconnected=disconnected,
            error=error
        )

    def get_cms_client_for_server(self, server_uuid: str = None, access_level: AccessLevel = None) -> Optional[CMS]:
        """קבלת CMS client עבור שרת ספציפי"""
        try:
            if server_uuid:
                server = self.__serverRepository.get_server_by_uuid(server_uuid)
            elif access_level:
                # חיפוש שרת לפי סוג (audio/video/blast_dial) לפי סדר היררכיה
                servers = self.__serverRepository.get_all_servers()
                # מסדרים לפי hierarchy_order ואז מחפשים שרת מתאים
                sorted_servers = sorted(servers, key=lambda s: s.hierarchy_order)
                server = next((s for s in sorted_servers if s.accessLevel == access_level and s.is_active and s.connection_status == 'connected'), None)
            else:
                # שרת ראשי כברירת מחדל, אם אין אז לפי סדר היררכיה
                servers = self.__serverRepository.get_all_servers()
                # קודם מחפשים שרת ראשי
                server = next((s for s in servers if s.is_primary and s.is_active and s.connection_status == 'connected'), None)
                
                # אם אין שרת ראשי, משתמשים בסדר היררכיה
                if not server:
                    sorted_servers = sorted(servers, key=lambda s: s.hierarchy_order)
                    server = next((s for s in sorted_servers if s.is_active and s.connection_status == 'connected'), None)
            
            if not server:
                return None
            
            # יצירת CMS client עם פרטי השרת
            base_url = f"https://{server.ip_address}:{server.port}"
            return CMS(
                base_url=base_url,
                username=server.username,
                password=server.password
            )
            
        except Exception as e:
            self.logger.error("Failed to get CMS client: %s", str(e))
            return None

    def _test_connection_direct(self, host: str, port: int, username: str, password: str) -> ConnectionTestResult:
        """בדיקת חיבור ישירה ל-CMS"""
        try:
            self.logger.info(f"Starting connection test to {host}:{port} with user {username}")
            start_time = time.time()
            
            try:
                self.logger.info("Creating CMS client...")
                base_url = f"https://{host}:{port}"
                cms = CMS(base_url=base_url, username=username, password=password)
                self.logger.info("CMS client created successfully")
                
                self.logger.info("Getting system info...")
                system_info = cms.get_system_info()
                self.logger.info(f"System info retrieved: {system_info}")
                
            except Exception as cms_error:
                self.logger.error(f"CMS connection failed: {str(cms_error)}")
                return ConnectionTestResult(
                    success=False,
                    message=f"שגיאת חיבור ל-CMS: {str(cms_error)}",
                    response_time_ms=None
                )
            
            response_time = (time.time() - start_time) * 1000  # ב-milliseconds
            
            result = ConnectionTestResult(
                success=True,
                message="חיבור הצליח",
                server_version=system_info.get('version', 'Unknown'),
                system_info=str(system_info),
                response_time_ms=response_time
            )
            
            self.logger.info(f"Connection test successful - response time: {response_time}ms")
            return result
            
        except Exception as e:
            self.logger.error(f"Unexpected error in connection test: {str(e)}")
            return ConnectionTestResult(
                success=False,
                message=f"שגיאת חיבור: {str(e)}",
                response_time_ms=None
            )

    def _test_connection_async(self, server_uuid: str):
        """בדיקת חיבור אסינכרונית ברקע ועדכון סטטוס ב-DB"""
        def background_test():
            try:
                # יצירת session חדש ל-thread
                from app.database import get_db
                db_gen = get_db()
                db = next(db_gen)
                
                try:
                    # קבלת פרטי השרת
                    server = self.__serverRepository.get_server_by_uuid(server_uuid)
                    if not server:
                        self.logger.error(f"Server {server_uuid} not found for async test")
                        return
                    
                    self.logger.info(f"Starting async connection test for server {server.server_name}")
                    
                    # בדיקת חיבור
                    result = self._test_connection_direct(
                        server.ip_address, server.port, server.username, server.password
                    )
                    
                    # עדכון סטטוס ב-DB
                    if result.success:
                        status = 'connected'
                        error = None
                        version = result.server_version
                        system_info = result.system_info
                        self.logger.info(f"Async connection test succeeded for {server.server_name}")
                    else:
                        status = 'error'
                        error = result.message
                        version = None
                        system_info = None
                        self.logger.warning(f"Async connection test failed for {server.server_name}: {result.message}")
                    
                    # עדכון ה-DB
                    self.__serverRepository.update_connection_status(
                        server_uuid, status, error, version, system_info, datetime.utcnow()
                    )
                    
                    self.logger.info(f"Async connection test completed for server {server_uuid}")
                    
                finally:
                    db.close()
                    
            except Exception as e:
                self.logger.error(f"Error in async connection test for server {server_uuid}: {str(e)}")
        
        # הפעלת ה-thread ברקע
        thread = threading.Thread(target=background_test, daemon=True)
        thread.start()
        self.logger.info(f"Async connection test thread started for server {server_uuid}")