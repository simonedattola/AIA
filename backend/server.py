"""FastAPI entrypoint for AIA Legnano platform."""
from contextlib import asynccontextmanager
from fastapi import FastAPI, APIRouter
from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from pathlib import Path
import os
import logging

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

from app.db import close_db, get_db
from app.paths import UPLOAD_DIR
from app.routes.public import router as public_router
from app.routes.admin import router as admin_router
from app.routes.portal import router as portal_router
from app import seed
from app.designations_scheduler import start_designations_scheduler, stop_designations_scheduler
from app.event_reminders_scheduler import start_event_reminders_scheduler, stop_event_reminders_scheduler
from app.security import warn_if_insecure_jwt_secret
from app.middleware import SecurityHeadersMiddleware
from app.indexes import ensure_indexes

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    warning = warn_if_insecure_jwt_secret()
    if warning:
        logger.warning(warning)
    try:
        await ensure_indexes(get_db())
    except Exception as exc:
        logger.warning("Index setup failed: %s", exc)
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
        logger.exception("Seed failed: %s", e)
    start_designations_scheduler()
    start_event_reminders_scheduler()
    yield
    stop_designations_scheduler()
    stop_event_reminders_scheduler()
    close_db()

app = FastAPI(title="AIA Legnano API", version="1.0", lifespan=lifespan)

api_router = APIRouter(prefix="/api")


@api_router.get("/")
async def root():
    return {"status": "ok", "service": "AIA Legnano API"}


@api_router.get("/health")
async def health():
    """Liveness + Mongo readiness."""
    db_ok = False
    try:
        db = get_db()
        await db.command("ping")
        db_ok = True
    except Exception as exc:
        logger.warning("Health DB ping failed: %s", exc)
    status = "ok" if db_ok else "degraded"
    code = 200 if db_ok else 503
    from fastapi.responses import JSONResponse

    return JSONResponse(
        status_code=code,
        content={"status": status, "service": "AIA Legnano API", "mongo": db_ok},
    )


app.include_router(api_router)
app.include_router(public_router)
app.include_router(admin_router)
app.include_router(portal_router)

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/api/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")


def _cors_origins() -> list[str]:
    raw = (os.environ.get("CORS_ORIGINS") or "").strip()
    if not raw or raw == "*":
        return ["http://localhost:3000", "http://127.0.0.1:3000"]
    return [o.strip() for o in raw.split(",") if o.strip()]


app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=_cors_origins(),
    allow_methods=["*"],
    allow_headers=["*"],
)



