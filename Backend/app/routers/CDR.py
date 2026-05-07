





# ============================================================================
# CDR Router - קבלת Call Detail Records משרת CMS
# ============================================================================

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
from logger import LoggerManager

CDRRouter = APIRouter()

# Pydantic model פשוט לקבלת CDR
class CDRData(BaseModel):
    call_id: str
    caller: str
    callee: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: Optional[int] = None
    call_type: str
    status: str
    meeting_uuid: Optional[str] = None
    server_name: Optional[str] = None
    additional_data: Optional[Dict[str, Any]] = None

# --- POST /cdr/send_sdr ---
# קבלת CDR משרת CMS (נתיב חיצוני)
@CDRRouter.post("/send_sdr", status_code=200)
def receive_cdr(cdr_data: CDRData):
    try:
        LoggerManager.get_logger().info(
            "Received CDR from CMS: call_id=%s, caller=%s, callee=%s, status=%s, server=%s",
            cdr_data.call_id, cdr_data.caller, cdr_data.callee, cdr_data.status, cdr_data.server_name
        )
        
        # כאן אפשר להוסיף לוגיקה כלשהי אם צריך (שליחה למערכת אחרת, וכו')
        # כרגע רק מדפיסים ללוג ומחזירים תגובה חיובית
        
        return {
            "success": True,
            "message": "CDR received successfully",
            "call_id": cdr_data.call_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as error:
        LoggerManager.get_logger().exception(
            "Failed to process CDR from CMS. Error: %s",
            str(error)
        )
        return {
            "success": False,
            "message": "Failed to process CDR",
            "error": str(error)
        }

# --- POST /cdr/cdr ---
# נתיב נוסף לתאימות
@CDRRouter.post("/cdr", status_code=200)
def create_cdr(cdr_data: CDRData):
    return receive_cdr(cdr_data)
    

