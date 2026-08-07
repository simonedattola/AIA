from __future__ import annotations

from typing import Optional
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Request
from fastapi.responses import FileResponse, Response
from slugify import slugify

from ...db import get_db
from ...security import require_admin, verify_password, create_token
from ...paths import UPLOAD_DIR
from ...member_roles import strip_sensitive_member_fields
from ...uploads import (
    save_upload,
    IMAGE_EXTENSIONS,
    ATTACHMENT_EXTENSIONS,
    DEFAULT_IMAGE_MAX_BYTES,
    max_bytes_for_attachment,
)
from ...rate_limit import client_ip, enforce_rate_limit
from ...models import (
    LoginRequest, TokenResponse, AdminInfo,
    SiteSettings, Page, Article, ArticleCreate, Event,
    Official, Member, MemberCreate, Designation,
    Document, Album, Testimonial, UtilityPolo, UtilityItem, EventUtilityMaterialUpdate,
    DesignationSyncRequest, ArticleCategoryCreate,
    GalleryImageCreate, GalleryImageUpdate,
)
from ...designations_sync import sync_from_aia_lombardia
from ...designations_import import import_designations_from_file, IMPORT_TEMPLATE_CSV
from ...designations_import_extract import SUPPORTED_EXTENSIONS
from ...members_import import import_members_from_file, IMPORT_TEMPLATE_CSV as MEMBERS_IMPORT_TEMPLATE_CSV
from ...sanitize import sanitize_html
from .deps import logger, now_iso

router = APIRouter()

# ---- Auth ----
@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, request: Request):
    enforce_rate_limit(
        f"admin-login:{client_ip(request)}",
        max_hits=10,
        window_seconds=300,
        detail="Troppi tentativi di login, riprova tra poco",
    )
    db = get_db()
    admin = await db.admin_users.find_one({"email": payload.email.lower()}, {"_id": 0})
    if not admin or not verify_password(payload.password, admin.get("passwordHash", "")):
        raise HTTPException(status_code=401, detail="Credenziali non valide")
    token = create_token({"sub": admin["email"], "role": "admin", "name": admin.get("name", "Admin")})
    return TokenResponse(token=token, admin=AdminInfo(email=admin["email"], name=admin.get("name", "Admin")))


@router.get("/me")
async def me(admin=Depends(require_admin)):
    return {"email": admin.get("sub"), "name": admin.get("name", "Admin")}


