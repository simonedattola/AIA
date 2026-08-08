"""FastAPI entrypoint for AIA Legnano platform."""
from fastapi import FastAPI, APIRouter, HTTPException
from fastapi.openapi.utils import get_openapi
from fastapi.responses import PlainTextResponse, JSONResponse, RedirectResponse, Response
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
from app.storage import uses_streamed_uploads
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

API_DESCRIPTION = """
Platform API for Arbitri AIA Legnano (**public**, **admin**, **portal**).

## Authentication

- **Admin** (`/api/admin/*` except `POST /api/admin/login`): JWT Bearer token from admin login.
- **Portal** (`/api/portal/*` except `POST /api/portal/login`): JWT Bearer token from member login.
- **Public** (`/api/public/*`): no auth (forms are rate-limited where configured).

Use **Authorize** in Swagger UI after obtaining a token.

Swagger UI: `/docs` · ReDoc: `/redoc` · Schema: `/openapi.json`
""".strip()

app = FastAPI(
    title="AIA Legnano API",
    version="1.0.0",
    description=API_DESCRIPTION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

_STARTED_AT = time.time()

# Health + legacy root
api_router = APIRouter(prefix="/api", tags=["health"])


@api_router.get("/")
async def root():
    """
    Health check for the AIA Legnano API.

    - **Returns:** `{status, service}` confirming the service is up.
    """
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


# Uploads: local StaticFiles, or GridFS / S3/R2 streamed by the app
if uses_streamed_uploads():
    from app import storage as upload_storage

    @app.get("/api/uploads/{name:path}")
    async def serve_object_upload(name: str):
        cdn = upload_storage.public_cdn_url(name)
        if cdn:
            return RedirectResponse(cdn, status_code=302)
        data = upload_storage.read_bytes(name)
        if data is None:
            raise HTTPException(404, "File non trovato")
        import mimetypes

        ctype = mimetypes.guess_type(name)[0] or "application/octet-stream"
        return Response(content=data, media_type=ctype)
else:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    app.mount("/api/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get("CORS_ORIGINS", "*").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)


def custom_openapi():
    """Build OpenAPI schema with JWT Bearer security scheme for Swagger UI."""
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="AIA Legnano API",
        version="1.0.0",
        description=API_DESCRIPTION,
        routes=app.routes,
    )
    openapi_schema.setdefault("components", {}).setdefault("securitySchemes", {})
    openapi_schema["components"]["securitySchemes"]["HTTPBearer"] = {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
        "description": (
            "JWT from `POST /api/admin/login` (admin) or "
            "`POST /api/portal/login` (member). "
            "Header: `Authorization: Bearer <token>`."
        ),
    }
    for path, methods in (openapi_schema.get("paths") or {}).items():
        if not isinstance(methods, dict):
            continue
        needs_auth = path.startswith("/api/admin/") or path.startswith("/api/portal/")
        is_login = path in {"/api/admin/login", "/api/portal/login"}
        if needs_auth and not is_login:
            for method, op in methods.items():
                if method.startswith("x-") or not isinstance(op, dict):
                    continue
                op.setdefault("security", [{"HTTPBearer": []}])
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


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

    try:
        from app.db_indexes import create_indexes

        await create_indexes()
    except Exception as e:
        logger.exception("Index creation failed: %s", e)

    start_designations_scheduler()
    start_event_reminders_scheduler()
    log_event(logger, "app_startup", phase="ready", outcome="success")


@app.on_event("shutdown")
async def on_shutdown():
    log_event(logger, "app_shutdown")
    stop_designations_scheduler()
    stop_event_reminders_scheduler()
    close_db()
