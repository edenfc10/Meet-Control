from fastapi import APIRouter, Depends, HTTPException
from app.security.TokenValidator import TokenValidator
from app.schema.user import UserOutput
import os
import io
import zipfile
from fastapi.responses import StreamingResponse

logsRouter = APIRouter()

only_super_admin = TokenValidator(allowed_roles=["super_admin"])

LOGS_PATH = "./logs"


@logsRouter.get("/dates")
def get_log_dates(user: UserOutput = Depends(only_super_admin)):
    if not os.path.exists(LOGS_PATH):
        return []
    dates = sorted(
        [d for d in os.listdir(LOGS_PATH) if os.path.isdir(os.path.join(LOGS_PATH, d))],
        reverse=True,
    )
    return dates


VALID_TYPES = {"info": "info.log", "warnings": "warnings.log", "errors": "errors.log"}


@logsRouter.get("/{date}/download")
def download_log(date: str, user: UserOutput = Depends(only_super_admin)):
    date_path = os.path.join(LOGS_PATH, date)
    if not os.path.isdir(date_path):
        raise HTTPException(status_code=404, detail="Log date not found")
 
    buffer = io.StringIO()
    for log_type, filename in VALID_TYPES.items():
        file_path = os.path.join(date_path, filename)
        buffer.write(f"===== {log_type.upper()} =====\n")
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                buffer.write(f.read())
        else:
            buffer.write("No entries\n")
        buffer.write("\n")
 
    content = buffer.getvalue().encode("utf-8")
    return StreamingResponse(
        io.BytesIO(content),
        media_type="text/plain",
        headers={"Content-Disposition": f"attachment; filename=logs_{date}.txt"},
    )

@logsRouter.get("/download-all")
def download_all_logs(user: UserOutput = Depends(only_super_admin)):
    if not os.path.exists(LOGS_PATH):
        raise HTTPException(status_code=404, detail="No logs found")
    
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for date_dir in os.listdir(LOGS_PATH):
            date_path = os.path.join(LOGS_PATH, date_dir)
            if os.path.isdir(date_path):
                for log_type, filename in VALID_TYPES.items():
                    file_path = os.path.join(date_path, filename)
                    if os.path.exists(file_path):
                        zip_file.write(file_path, os.path.join(date_dir, filename))
    
    buffer.seek(0)
    return StreamingResponse(
        buffer,
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=logs.zip"},
    )

@logsRouter.get("/{date}/{log_type}")
def get_log_by_date_and_type(date: str, log_type: str, user: UserOutput = Depends(only_super_admin)):
    if log_type not in VALID_TYPES:
        raise HTTPException(status_code=400, detail=f"Invalid log type. Use: {list(VALID_TYPES.keys())}")
    log_file = os.path.join(LOGS_PATH, date, VALID_TYPES[log_type])
    if not os.path.exists(log_file):
        return {"date": date, "type": log_type, "lines": []}
    with open(log_file, "r", encoding="utf-8") as f:
        lines = f.readlines()
    return {"date": date, "type": log_type, "lines": [l.rstrip("\n") for l in lines]}
