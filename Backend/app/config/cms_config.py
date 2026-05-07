# ============================================================================
# CMS Configuration - הגדרות שרת Cisco Meeting Server
# ============================================================================
# קובץ זה מכיל את כתובות השרתים ופרטי הגישה ל-CMS
# ============================================================================

import os
from typing import List, Dict, Optional

class CMSConfig:
    """קלאס לניהול הגדרות CMS"""
    
    # כתובות שרתי CMS (ניתן להוסיף עוד שרתים)
    CMS_SERVERS = {
        "primary": {
            "host": os.getenv("CMS_PRIMARY_HOST") or "192.168.20.150",
            "port": int(os.getenv("CMS_PRIMARY_PORT") or "455"),
            "username": os.getenv("CMS_PRIMARY_USER") or "admin",
            "password": os.getenv("CMS_PRIMARY_PASSWORD") or "S@p180tech"
        },
        "secondary": {
            "host": os.getenv("CMS_SECONDARY_HOST") or "192.168.1.30",
            "port": int(os.getenv("CMS_SECONDARY_PORT") or "8443"),
            "username": os.getenv("CMS_SECONDARY_USER") or "admin",
            "password": os.getenv("CMS_SECONDARY_PASSWORD") or "admin"
        }
    }
    
    @classmethod
    def get_cms_server(cls, server_name: str = "primary") -> Dict:
        """קבלת פרטי שרת CMS"""
        if server_name not in cls.CMS_SERVERS:
            raise ValueError(f"CMS server '{server_name}' not found")
        
        server = cls.CMS_SERVERS[server_name]
        return {
            "base_url": f"https://{server['host']}:{server['port']}",
            "username": server["username"],
            "password": server["password"]
        }
    
    @classmethod
    def get_all_cms_servers(cls) -> List[str]:
        """קבלת רשימת כל שרתי ה-CMS הזמינים"""
        return list(cls.CMS_SERVERS.keys())
    
    @classmethod
    def is_development_mode(cls) -> bool:
        """בדיקה אם אנחנו בסביבת פיתוח"""
        return os.getenv("ENV", "development").lower() == "development"
    
    @classmethod
    def test_connection(cls, server_name: str = "primary") -> bool:
        """בדיקת חיבור לשרת CMS"""
        # בסביבת פיתוח, לא ננסה להתחבר ל-CMS אלא אם כן מפורש אחרת
        if cls.is_development_mode() and not os.getenv("FORCE_CMS_CONNECTION"):
            return False
            
        try:
            from app.service.cms import CMS
            server_config = cls.get_cms_server(server_name)
            cms = CMS(
                base_url=server_config["base_url"],
                username=server_config["username"],
                password=server_config["password"]
            )
            return cms.test_connection()
        except Exception:
            return False
