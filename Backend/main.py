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
from app.routers.CDR import CDRRouter
from logger import LoggerManager
from app.security.superAdminTest import SuperAdminTest

# מטא-דאטה לתיעוד OpenAPI (Swagger UI)
tags_metadata = [
    {"name": "auth", "description": "Authentication endpoints (login/signup)"},
    {"name": "users", "description": "User management endpoints"},
    {"name": "groups", "description": "Group management & access control"},
    {"name": "servers", "description": "Server management endpoints"},
    {"name": "protected", "description": "Protected endpoints requiring login"},
    {"name": "cdr", "description": "Call Detail Record endpoints"},
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

app = FastAPI(lifespan=lifespan, openapi_tags=tags_metadata)

# מנגנון החלפה אוטומטית בין CMS ל-MOCK
# הגדר USE_MOCK=true במשתני סביבה כדי להשתמש ב-MOCK במקום CMS אמיתי
USE_MOCK = os.getenv("USE_MOCK", "false").lower() == "true"

if USE_MOCK:
    from app.routers.cms_mock import cmsMockRouter
    app.include_router(router=cmsMockRouter, tags=["cms_mock"], prefix="/cms_mock")
    print("🔧 CMS MOCK Mode Enabled")
else:
    print("🌐 Real CMS Mode Enabled")

# הגדרת logging - כל ההודעות יודפסו גם ל-stdout (Docker logs)


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

# רשימת הכתובות שמותר להן לגשת לשרת (CORS whitelist)
origins = [
    "http://localhost:5173",  # Frontend של Vite - פורט ברירת מחדל
    "http://127.0.0.1:5173",
    "http://192.168.1.30:5173",  # כתובת IP מקומית
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
app.include_router(router=CDRRouter, tags=["cdr"], prefix="/cdr")
# # app.include_router(router=cmsMockRouter, tags=["cms_mock"], prefix="/cms_mock")  # הפעל MOCK במקום CMS אמיתי
