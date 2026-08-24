from app.event_access import (
    event_invited_members_query,
    member_invited_to_event,
)


def test_empty_invite_means_all():
    ev = {"invitedMemberIds": [], "invitedRoleGroups": []}
    assert member_invited_to_event(ev, "m1") is True


def test_selective_invite_by_id():
    ev = {"invitedMemberIds": ["m1", "m2"], "invitedRoleGroups": []}
    assert member_invited_to_event(ev, "m1") is True
    assert member_invited_to_event(ev, "m3") is False


def test_selective_invite_by_role_group():
    ev = {"invitedMemberIds": [], "invitedRoleGroups": ["AE"]}
    ae = {"id": "m1", "role": "AE", "memberRole": "arbitro"}
    aa = {"id": "m2", "role": "AA", "memberRole": "assistente"}
    assert member_invited_to_event(ev, "m1", member=ae) is True
    assert member_invited_to_event(ev, "m2", member=aa) is False
    assert member_invited_to_event(ev, "m1") is False


def test_event_invited_members_query_role_groups():
    ev = {"invitedMemberIds": [], "invitedRoleGroups": ["OT", "ors"]}
    q = event_invited_members_query(ev)
    assert "$or" in q


def test_legacy_related_member_ids():
    ev = {"relatedMemberIds": ["m9"]}
    assert member_invited_to_event(ev, "m9") is True


def test_public_visibility():
    from app.event_access import event_visible_on_public_site, public_events_query

    assert event_visible_on_public_site({"portalOnly": False}) is True
    assert event_visible_on_public_site({"portalOnly": True}) is False
    q = public_events_query()
    assert "$and" in q
    assert {"portalOnly": {"$ne": True}} in q["$and"]
