"""FastAPI entrypoint for AIA Legnano platform."""
from fastapi import FastAPI, APIRouter
from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from pathlib import Path
import os
import logging

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

from app.db import get_db, close_db
from app.paths import UPLOAD_DIR
from app.routes.public import router as public_router
from app.routes.admin import router as admin_router
from app.routes.portal import router as portal_router
from app import seed
from app.designations_scheduler import start_designations_scheduler, stop_designations_scheduler
from app.event_reminders_scheduler import start_event_reminders_scheduler, stop_event_reminders_scheduler

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(title="AIA Legnano API", version="1.0")

# Health
api_router = APIRouter(prefix="/api")


@api_router.get("/")
async def root():
    return {"status": "ok", "service": "AIA Legnano API"}


app.include_router(api_router)
app.include_router(public_router)
app.include_router(admin_router)
app.include_router(portal_router)

# Uploads static
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/api/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def on_startup():
    logger.info("Seeding database…")
    try:
        await seed.run_all()
        from app.portal_credentials import (
            backfill_portal_passwords,
            enable_portal_access_for_directory,
            purge_fictitious_meccanografici,
        )
        await purge_fictitious_meccanografici()
        await backfill_portal_passwords()
        await enable_portal_access_for_directory()
        logger.info("Seed complete.")
    except Exception as e:
        logger.exception(f"Seed failed: {e}")
    start_designations_scheduler()
    start_event_reminders_scheduler()


@app.on_event("shutdown")
async def on_shutdown():
    stop_designations_scheduler()
    stop_event_reminders_scheduler()
    close_db()
