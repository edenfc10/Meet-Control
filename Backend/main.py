# ============================================================================
# Main Application Entry Point - FastAPI
# ============================================================================
# קובץ זה מגדיר את אפליקציית FastAPI הראשית.
# תפקידים:
#   1. Lifespan - אתחול DB + יצירת super_admin בהפעלה ראשונה
#   2. CORS - הגדרת גישה מה-frontend (React/Vite בפורט 5173)
#   3. Routers - רישום כל הנתיבים (auth, users, groups, meetings, protected)
#
# נתיבי ה-API:
#   /auth/*       - הרשמה והתחברות
#   /users/*      - ניהול משתמשים (CRUD)
#   /groups/*     - ניהול קבוצות וחברויות
#   /meetings/*   - ניהול ישיבות
#   /protected/*  - נתיבים מוגנים (בדיקת token)
# ============================================================================

import os

from time import perf_counter

from fastapi import FastAPI , Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from app.util.init_db import create_tables
from contextlib import asynccontextmanager
import logging
import sys
from app.routers.auth import authRouter
from app.routers.user import userRouter
from app.routers.group import groupRouter
from app.routers.meeting import meetingRouter
from app.routers.favorite import favoriteRouter
from app.routers.protect import protectRouter
from app.routers.server import serverRouter
from logger import LoggerManager
from app.schema.user import UserOutput
from app.security.auth import AuthHand

from app.security.superAdminTest import SuperAdminTest

# הגדרת logging - כל ההודעות יודפסו גם ל-stdout (Docker logs)

# מטא-דאטה לתיעוד OpenAPI (Swagger UI)
tags_metadata = [
    {"name": "auth", "description": "Authentication endpoints (login/signup)"},
    {"name": "users", "description": "User management endpoints"},
    {"name": "groups", "description": "Group management & access control"},
    {"name": "servers", "description": "Server management endpoints"},
    {"name": "protected", "description": "Protected endpoints requiring login"},
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan handler - אתחול והגדרות ראשוניות של האפליקציה.
    בפעולה זו נוצרת טבלת DB + super_admin. בסיום: רושמים הודעת shutdown.
    """
    # Keep a high backup_count so every 10MB rollover creates another file on the same day.
    LoggerManager.initialize(path_prefix="./logs", size_mb=10, backup_count=1000, retention_days=30)  # אתחול מערכת הלוגים
    create_tables()                       # יצירת/אימות טבלאות ב-DB
    SuperAdminTest.create_super_admin()    # יצירת super admin ראשוני אם חסר
    yield                                 # האפליקציה רצה כאן
   


# יצירת אפליקציית FastAPI עם lifespan ו-tags ל-Swagger

app = FastAPI(lifespan=lifespan, openapi_tags=tags_metadata)


@app.middleware("http")
async def request_audit_log(request: Request, call_next):
    """Audit logs all mutating API requests (POST/PUT/PATCH/DELETE)."""
    method = request.method
    path = request.url.path
    is_mutation = method in {"POST", "PUT", "PATCH", "DELETE"}

    if not is_mutation:
        return await call_next(request)

    start = perf_counter()
    client_ip = request.client.host if request.client else "unknown"
    query_string = request.url.query or "-"
    user_ctx = "anonymous"

    # קריאת token מ-cookie (httpOnly) או מ-Authorization header
    token = request.cookies.get("access_token", "")
    if not token:
        auth_header = request.headers.get("authorization", "")
        if auth_header.lower().startswith("bearer "):
            token = auth_header.split(" ", 1)[1].strip()
    if token:
        payload = AuthHand.decode_jwt(token)
        if payload:
            user_ctx = f"{payload.get('s_id', 'unknown')}:{payload.get('role', 'unknown')}"

    try:
        response = await call_next(request)
    except Exception as error:
        elapsed_ms = (perf_counter() - start) * 1000
        LoggerManager.get_logger().exception(
            "AUDIT mutation %s %s | query=%s | user=%s ip=%s | status=500 | duration_ms=%.2f | error=%s",
            method,
            path,
            query_string,
            user_ctx,
            client_ip,
            elapsed_ms,
            str(error),
        )
        raise

    elapsed_ms = (perf_counter() - start) * 1000
    LoggerManager.get_logger().info(
        "AUDIT mutation %s %s | query=%s | user=%s ip=%s | status=%s | duration_ms=%.2f",
        method,
        path,
        query_string,
        user_ctx,
        client_ip,
        response.status_code,
        elapsed_ms,
    )
    return response

# רשימת הכתובות שמותר להן לגשת לשרת (CORS whitelist)
origins = [
    "http://localhost:5173",  # Frontend של Vite - פורט ברירת מחדל
    "http://127.0.0.1:5173",
]

# הגדרת CORS - מאפשר ל-Frontend לתקשר עם ה-API
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,            # מאפשר גישה רק מהכתובות שמעל
    allow_credentials=True,           # מאפשר שליחת עוגיות ו-Headers של Auth
    allow_methods=["*"],              # מאפשר את כל סוגי הפעולות (GET, POST וכו')
    allow_headers=["*"],              # מאפשר את כל ה-Headers
)

# רישום כל ה-Routers - כל קבוצות endpoints עם prefix משלה
app.include_router(router=authRouter, tags=["auth"], prefix="/auth")
app.include_router(router=userRouter, tags=["users"], prefix="/users")
app.include_router(router=protectRouter, tags=["protected"], prefix="/protected")
app.include_router(router=groupRouter, tags=["groups"], prefix="/groups")
app.include_router(router=meetingRouter, tags=["meetings"], prefix="/meetings")
app.include_router(router=serverRouter, tags=["servers"], prefix="/servers")
app.include_router(router=favoriteRouter, tags=["favorites"], prefix="/favorites")
