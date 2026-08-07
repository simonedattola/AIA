"""Admin API package — /api/admin/*."""
from fastapi import APIRouter

from . import (
    auth,
    dashboard,
    settings,
    pages,
    articles,
    events,
    officials,
    members,
    designations,
    leads,
    messages,
    documents,
    utility,
    albums,
    testimonials,
    gallery,
    uploads,
    comunicazioni,
)

router = APIRouter(prefix="/api/admin", tags=["admin"])

for _mod in (
    auth,
    dashboard,
    settings,
    pages,
    articles,
    events,
    officials,
    members,
    designations,
    leads,
    messages,
    documents,
    utility,
    albums,
    testimonials,
    gallery,
    uploads,
    comunicazioni,
):
    router.include_router(_mod.router)
