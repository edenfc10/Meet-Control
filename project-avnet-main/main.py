from fastapi import FastAPI , Depends
from fastapi.middleware.cors import CORSMiddleware
from app.util.init_db import create_tables
from contextlib import asynccontextmanager
import logging
import sys
from app.routers.auth import authRouter
from app.routers.user import userRouter
from app.routers.protect import protectRouter, get_current_user
from app.routers.mador import madorRouter
from app.schema.user import UserOutput

from app.security.superAdminTest import SuperAdminTest

# Configure logging to show all levels
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout,
    force=True
)

logger = logging.getLogger(__name__)

tags_metadata = [
    {"name": "auth", "description": "Authentication endpoints (login/signup)"},
    {"name": "users", "description": "User management endpoints"},
    {"name": "madors", "description": "Mador management & access control"},
    {"name": "protected", "description": "Protected endpoints requiring login"},
]

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting application...")
    create_tables()
    logger.info("Database tables verified")
    SuperAdminTest.create_super_admin()
    logger.info("Application startup complete\n")
    yield
    logger.info("Shutting down application")

app = FastAPI(lifespan=lifespan, openapi_tags=tags_metadata)

# רשימת הכתובות שמותר להן לגשת לשרת שלך
origins = [
    "http://localhost:5173",  # ה-Frontend של Vite
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,            # מאפשר גישה רק ל-React שלך
    allow_credentials=True,           # מאפשר שליחת עוגיות ו-Headers של Auth
    allow_methods=["*"],              # מאפשר את כל סוגי הפעולות (GET, POST וכו')
    allow_headers=["*"],              # מאפשר את כל ה-Headers
)

app.include_router(router=authRouter, tags=["auth"], prefix="/auth")
app.include_router(router=userRouter, tags=["users"], prefix="/users")
app.include_router(router=madorRouter, tags=["madors"], prefix="/madors")
app.include_router(router=protectRouter, tags=["protected"], prefix="/protected")