from app.event_access import (
    event_invited_member_ids,
    event_visible_on_public_site,
    member_invited_to_event,
    public_events_query,
)


def test_empty_invite_means_all():
    ev = {"invitedMemberIds": []}
    assert member_invited_to_event(ev, "m1") is True
    assert member_invited_to_event(ev, "m2") is True


def test_selective_invite():
    ev = {"invitedMemberIds": ["m1", "m2"]}
    assert member_invited_to_event(ev, "m1") is True
    assert member_invited_to_event(ev, "m3") is False


def test_legacy_related_member_ids():
    ev = {"relatedMemberIds": ["m9"]}
    assert event_invited_member_ids(ev) == ["m9"]
    assert member_invited_to_event(ev, "m9") is True


def test_public_visibility():
    assert event_visible_on_public_site({"portalOnly": False}) is True
    assert event_visible_on_public_site({"portalOnly": True}) is False
    # Default includes current football season window
    q = public_events_query()
    assert q.get("portalOnly") == {"$ne": True} or (
        "$and" in q and {"portalOnly": {"$ne": True}} in q["$and"]
    )
    q_all = public_events_query(current_season=False)
    assert q_all == {"portalOnly": {"$ne": True}}
