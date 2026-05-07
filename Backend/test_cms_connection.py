#!/usr/bin/env python3
# ============================================================================
# CMS Connection Test - בדיקת חיבור ל-CMS מעבדה
# ============================================================================

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.config.cms_config import CMSConfig
from app.service.cms import CMS
import logging

# הגדרת logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_cms_connection():
    """בדיקת חיבור ל-CMS מעבדה"""
    
    print("🔍 בודק חיבור ל-CMS מעבדה...")
    print("=" * 50)
    
    # בדיקת הגדרות סביבה
    print(f"📍 CMS Primary Host: {os.getenv('CMS_PRIMARY_HOST', '192.168.1.24')}")
    print(f"📍 CMS Primary Port: {os.getenv('CMS_PRIMARY_PORT', '8443')}")
    print(f"📍 CMS Primary User: {os.getenv('CMS_PRIMARY_USER', 'admin')}")
    print(f"📍 ENV: {os.getenv('ENV', 'development')}")
    print(f"📍 FORCE_CMS_CONNECTION: {os.getenv('FORCE_CMS_CONNECTION', 'not set')}")
    print()
    
    # בדיקת חיבור לשרת ראשי
    try:
        print("🔗 מנסה להתחבר לשרת CMS ראשי...")
        server_config = CMSConfig.get_cms_server("primary")
        print(f"   📡 Base URL: {server_config['base_url']}")
        print(f"   👤 Username: {server_config['username']}")
        
        cms = CMS(
            base_url=server_config["base_url"],
            username=server_config["username"],
            password=server_config["password"]
        )
        
        # בדיקת חיבור בסיסית
        if cms.test_connection():
            print("✅ חיבור ל-CMS ראשי הצליח!")
            
            # נסה לקבל מידע מערכת
            try:
                system_info = cms.get_system_info()
                print(f"   📊 מידע מערכת: {system_info}")
            except Exception as e:
                print(f"   ⚠️  לא ניתן לקבל מידע מערכת: {e}")
            
            # נסה לקבל שיחות פעילות
            try:
                active_calls = cms.get_active_calls()
                print(f"   📞 שיחות פעילות: {len(active_calls)}")
                if active_calls:
                    print(f"   📋 שיחה ראשונה: {active_calls[0].get('callId', 'N/A')}")
            except Exception as e:
                print(f"   ⚠️  לא ניתן לקבל שיחות פעילות: {e}")
            
            # נסה לקבל CoSpaces
            try:
                cospaces = cms.list_cospaces()
                print(f"   🏢 CoSpaces: {len(cospaces)}")
                if cospaces:
                    print(f"   📋 CoSpace ראשון: {cospaces[0].get('name', 'N/A')}")
            except Exception as e:
                print(f"   ⚠️  לא ניתן לקבל CoSpaces: {e}")
                
        else:
            print("❌ חיבור ל-CMS ראשי נכשל!")
            return False
            
    except Exception as e:
        print(f"❌ שגיאה בחיבור ל-CMS ראשי: {e}")
        return False
    
    print()
    
    # בדיקת חיבור לשרת משני (אם מוגדר)
    try:
        print("🔗 מנסה להתחבר לשרת CMS משני...")
        server_config = CMSConfig.get_cms_server("secondary")
        print(f"   📡 Base URL: {server_config['base_url']}")
        
        cms_secondary = CMS(
            base_url=server_config["base_url"],
            username=server_config["username"],
            password=server_config["password"]
        )
        
        if cms_secondary.test_connection():
            print("✅ חיבור ל-CMS משני הצליח!")
        else:
            print("❌ חיבור ל-CMS משני נכשל!")
            
    except Exception as e:
        print(f"❌ שגיאה בחיבור ל-CMS משני: {e}")
    
    print()
    print("🎯 בדיקה הסתיימה!")
    print("=" * 50)
    print("💡 אם החיבור עבד, המערכת מוכנה לעבודה עם CMS אמיתי!")
    print()
    print("📝 הצעדים הבאים:")
    print("   1. הפעל את הבאקנד: docker compose up --build")
    print("   2. פתח Swagger: http://localhost:8000/docs")
    print("   3. נסה את ה-endpoints: GET /meetings/calls/active")
    print("   4. נסה ליצור CoSpace: POST /meetings/cospaces")
    
    return True

if __name__ == "__main__":
    test_cms_connection()
