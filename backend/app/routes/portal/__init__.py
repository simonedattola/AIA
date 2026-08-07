"""Portal API package — /api/portal/*."""
from fastapi import APIRouter

from . import (
    auth,
    dashboard,
    calendario,
    storico,
    utility,
    documenti,
    comunicazioni,
    premi,
    media,
    messaging,
    gallery,
    profile,
    preferiti,
    admin_presenze,
    admin_comunicazioni
)

router = APIRouter(prefix="/api/portal", tags=["portal"])

for _mod in (
    auth,
    dashboard,
    calendario,
    storico,
    utility,
    documenti,
    comunicazioni,
    premi,
    media,
    messaging,
    gallery,
    profile,
    preferiti,
    admin_presenze,
    admin_comunicazioni
):
    router.include_router(_mod.router)
