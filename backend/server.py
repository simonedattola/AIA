"""FastAPI entrypoint for AIA Legnano platform."""
from fastapi import FastAPI, APIRouter
from fastapi.openapi.utils import get_openapi
from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from pathlib import Path
import os
import logging

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

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

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

API_DESCRIPTION = """
Platform API for Arbitri AIA Legnano (**public**, **admin**, **portal**).

## Authentication

- **Admin** (`/api/admin/*` except `POST /api/admin/login`): JWT Bearer token from admin login.
- **Portal** (`/api/portal/*` except `POST /api/portal/login`): JWT Bearer token from member login.
- **Public** (`/api/public/*`): no auth (forms are rate-limited where configured).

Use **Authorize** in Swagger UI after obtaining a token.
""".strip()

app = FastAPI(
    title="AIA Legnano API",
    version="1.0.0",
    description=API_DESCRIPTION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Health
api_router = APIRouter(prefix="/api", tags=["health"])


@api_router.get("/")
async def root():
    """
    Health check for the AIA Legnano API.

    - **Returns:** `{status, service}` confirming the service is up.
    """
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
    # Mark protected path prefixes so Swagger "Authorize" applies cleanly
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
