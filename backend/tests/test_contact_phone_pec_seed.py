"""Migrazione one-shot telefono fisso → cellulare + PEC."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.seed import ensure_contact_phone_and_pec


@pytest.mark.asyncio
async def test_replaces_legacy_landline_and_sets_pec():
    db = MagicMock()
    db.site_settings.find_one = AsyncMock(
        return_value={"id": "site-settings", "phone": "+39 0331 541541", "pecEmail": ""}
    )
    db.site_settings.update_one = AsyncMock()

    with (
        patch("app.seed.get_db", return_value=db),
        patch("app.seed._seed_flag", new=AsyncMock(return_value=False)),
        patch("app.seed._set_seed_flag", new=AsyncMock()) as set_flag,
    ):
        await ensure_contact_phone_and_pec()

    db.site_settings.update_one.assert_awaited()
    args, kwargs = db.site_settings.update_one.await_args
    assert args[0] == {"id": "site-settings"}
    assert kwargs["upsert"] is True
    assert args[1]["$set"]["phone"] == "335-655-9488"
    assert args[1]["$set"]["pecEmail"] == "aia.legnano@pec.it"
    set_flag.assert_awaited_with("contact_phone_pec_2026_11")


@pytest.mark.asyncio
async def test_skips_when_flag_already_set():
    db = MagicMock()
    db.site_settings.find_one = AsyncMock()
    db.site_settings.update_one = AsyncMock()

    with (
        patch("app.seed.get_db", return_value=db),
        patch("app.seed._seed_flag", new=AsyncMock(return_value=True)),
        patch("app.seed._set_seed_flag", new=AsyncMock()) as set_flag,
    ):
        await ensure_contact_phone_and_pec()

    db.site_settings.find_one.assert_not_awaited()
    db.site_settings.update_one.assert_not_awaited()
    set_flag.assert_not_awaited()


@pytest.mark.asyncio
async def test_keeps_custom_phone_but_fills_missing_pec():
    db = MagicMock()
    db.site_settings.find_one = AsyncMock(
        return_value={
            "id": "site-settings",
            "phone": "339 111 2222",
            "pecEmail": None,
        }
    )
    db.site_settings.update_one = AsyncMock()

    with (
        patch("app.seed.get_db", return_value=db),
        patch("app.seed._seed_flag", new=AsyncMock(return_value=False)),
        patch("app.seed._set_seed_flag", new=AsyncMock()),
    ):
        await ensure_contact_phone_and_pec()

    args, _ = db.site_settings.update_one.await_args
    assert "phone" not in args[1]["$set"]
    assert args[1]["$set"]["pecEmail"] == "aia.legnano@pec.it"
