from datetime import datetime, timedelta, timezone

from app.portal_messaging import MESSAGE_EDIT_WINDOW, message_editable


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat()


def test_message_editable_within_window():
    now = datetime(2026, 5, 21, 12, 0, tzinfo=timezone.utc)
    created = now - timedelta(minutes=10)
    msg = {
        "mittenteId": "m1",
        "tipo": "text",
        "createdAt": _iso(created),
    }
    assert message_editable(msg, "m1", _iso(now)) is True


def test_message_editable_after_window():
    now = datetime(2026, 5, 21, 12, 0, tzinfo=timezone.utc)
    created = now - MESSAGE_EDIT_WINDOW - timedelta(seconds=1)
    msg = {
        "mittenteId": "m1",
        "tipo": "text",
        "createdAt": _iso(created),
    }
    assert message_editable(msg, "m1", _iso(now)) is False


def test_message_editable_not_sender():
    now = datetime(2026, 5, 21, 12, 0, tzinfo=timezone.utc)
    msg = {
        "mittenteId": "m1",
        "tipo": "text",
        "createdAt": _iso(now),
    }
    assert message_editable(msg, "m2", _iso(now)) is False


def test_message_editable_deleted_or_attachment():
    now = datetime(2026, 5, 21, 12, 0, tzinfo=timezone.utc)
    base = {"mittenteId": "m1", "createdAt": _iso(now)}
    assert (
        message_editable(
            {**base, "tipo": "text", "deletedAt": _iso(now)}, "m1", _iso(now)
        )
        is False
    )
    assert message_editable({**base, "tipo": "image"}, "m1", _iso(now)) is False
