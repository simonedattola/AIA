"""MongoDB indexes for hot query paths."""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


async def ensure_indexes(db) -> None:
    """Idempotent index creation for production query patterns."""
    specs: list[tuple[str, list[tuple[str, int]], dict]] = [
        ("members", [("slug", 1)], {"unique": True, "name": "members_slug_unique"}),
        ("members", [("meccanografico", 1)], {"name": "members_meccanografico"}),
        ("members", [("memberRole", 1), ("lastName", 1), ("firstName", 1)], {"name": "members_role_name"}),
        ("articles", [("slug", 1)], {"unique": True, "name": "articles_slug_unique"}),
        ("articles", [("status", 1), ("publishedAt", -1)], {"name": "articles_status_published"}),
        ("articles", [("relatedMemberIds", 1)], {"name": "articles_related_members"}),
        ("pages", [("slug", 1)], {"unique": True, "name": "pages_slug_unique"}),
        ("events", [("date", 1)], {"name": "events_date"}),
        ("events", [("invitedMemberIds", 1)], {"name": "events_invited"}),
        ("designations", [("matchDate", -1)], {"name": "designations_match_date"}),
        ("designations", [("memberId", 1), ("matchDate", -1)], {"name": "designations_member_date"}),
        ("designations", [("memberSlug", 1), ("matchDate", -1)], {"name": "designations_slug_date"}),
        ("designations", [("status", 1), ("matchDate", 1)], {"name": "designations_status_date"}),
        ("gallery_images", [("status", 1), ("sortOrder", 1)], {"name": "gallery_status_order"}),
        ("gallery_images", [("memberId", 1)], {"name": "gallery_member"}),
        ("gallery_images", [("memberIds", 1)], {"name": "gallery_member_ids"}),
        ("presenze_evento", [("eventId", 1), ("memberId", 1)], {"unique": True, "name": "presenze_event_member"}),
        ("messaggi_interni", [("chatId", 1), ("createdAt", -1)], {"name": "messaggi_chat_created"}),
        ("comunicazioni_interne", [("createdAt", -1)], {"name": "comunicazioni_created"}),
        ("leads", [("createdAt", -1)], {"name": "leads_created"}),
        ("contact_messages", [("createdAt", -1)], {"name": "contacts_created"}),
    ]
    created = 0
    for coll_name, keys, opts in specs:
        coll = getattr(db, coll_name)
        try:
            await coll.create_index(keys, **opts)
            created += 1
        except Exception as exc:
            logger.warning("Index %s on %s skipped: %s", opts.get("name"), coll_name, exc)
    logger.info("Mongo indexes ensured (%s definitions)", created)
