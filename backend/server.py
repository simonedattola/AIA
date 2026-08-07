"""FastAPI entrypoint for AIA Legnano platform."""
from fastapi import FastAPI, APIRouter
from fastapi.responses import PlainTextResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from pathlib import Path
from datetime import datetime, timezone
import os
import logging
import time

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

from app.logging_config import configure_logging, log_event

configure_logging()

from app.db import get_db, close_db
from app.paths import UPLOAD_DIR
from app.routes.public import router as public_router
from app.routes.admin import router as admin_router
from app.routes.portal import router as portal_router
from app import seed
from app.designations_scheduler import (
    start_designations_scheduler,
    stop_designations_scheduler,
)
from app.event_reminders_scheduler import (
    start_event_reminders_scheduler,
    stop_event_reminders_scheduler,
)

logger = logging.getLogger(__name__)

app = FastAPI(title="AIA Legnano API", version="1.0")

_STARTED_AT = time.time()

# Health + legacy root
api_router = APIRouter(prefix="/api", tags=["health"])


@api_router.get("/")
async def root():
    """Legacy health-ish root used by older clients."""
    return {"status": "ok", "service": "AIA Legnano API"}


@api_router.get("/health")
async def health():
    """
    Liveness/readiness probe with dependency status.

    - **Returns:** `{status, timestamp, services}` — HTTP 200 when healthy,
      HTTP 503 when the database is unreachable.
    """
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    db_status = "disconnected"
    overall = "unhealthy"

    try:
        db = get_db()
        await db.command("ping")
        db_status = "connected"
        overall = "healthy"
    except Exception as exc:
        log_event(
            logger,
            "health_check_failed",
            level=logging.ERROR,
            dependency="database",
            error=str(exc),
        )

    payload = {
        "status": overall,
        "timestamp": timestamp,
        "services": {
            "database": db_status,
            "cache": "N/A",
        },
    }
    code = 200 if overall == "healthy" else 503
    return JSONResponse(content=payload, status_code=code)


app.include_router(api_router)
app.include_router(public_router)
app.include_router(admin_router)
app.include_router(portal_router)


@app.get("/metrics", response_class=PlainTextResponse, include_in_schema=False)
async def metrics():
    """Minimal Prometheus-style metrics for uptime scrapers (Datadog/New Relic/etc.)."""
    uptime = max(0.0, time.time() - _STARTED_AT)
    # Best-effort DB probe for gauge (0/1)
    db_up = 0
    try:
        await get_db().command("ping")
        db_up = 1
    except Exception:
        db_up = 0
    lines = [
        "# HELP aia_api_up 1 if the API process is running",
        "# TYPE aia_api_up gauge",
        "aia_api_up 1",
        "# HELP aia_api_uptime_seconds Process uptime in seconds",
        "# TYPE aia_api_uptime_seconds gauge",
        f"aia_api_uptime_seconds {uptime:.3f}",
        "# HELP aia_api_database_up 1 if MongoDB ping succeeds",
        "# TYPE aia_api_database_up gauge",
        f"aia_api_database_up {db_up}",
        "",
    ]
    return "\n".join(lines)


# Uploads static
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/api/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get("CORS_ORIGINS", "*").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def on_startup():
    log_event(logger, "app_startup", phase="seed")
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
        log_event(logger, "app_startup", phase="seed_complete", outcome="success")
    except Exception as e:
        log_event(
            logger,
            "app_startup",
            level=logging.ERROR,
            phase="seed",
            outcome="failed",
            error=str(e),
        )
        logger.exception("Seed failed: %s", e)
    start_designations_scheduler()
    start_event_reminders_scheduler()
    log_event(logger, "app_startup", phase="ready", outcome="success")


@app.on_event("shutdown")
async def on_shutdown():
    log_event(logger, "app_shutdown")
    stop_designations_scheduler()
    stop_event_reminders_scheduler()
    close_db()
