"""MongoDB indexes for hot query paths (idempotent).

Field names match the live AIA Legnano schema (not legacy placeholders):
- articles: status + publishedAt / createdAt
- designations: memberId + matchDate, refereeSection + matchDate
- members: email (sparse), meccanografico, slug
- events: date, portalOnly + date
"""

from __future__ import annotations

import logging
from typing import Any

from .db import get_db

logger = logging.getLogger(__name__)

# (collection, keys, create_index kwargs)
INDEX_SPECS: list[tuple[str, list[tuple[str, int]], dict[str, Any]]] = [
    # Articles
    ("articles", [("createdAt", -1)], {"name": "articles_created"}),
    ("articles", [("publishedAt", -1)], {"name": "articles_published_at"}),
    (
        "articles",
        [("status", 1), ("publishedAt", -1)],
        {"name": "articles_status_published"},
    ),
    ("articles", [("slug", 1)], {"unique": True, "name": "articles_slug_unique"}),
    ("articles", [("relatedMemberIds", 1)], {"name": "articles_related_members"}),
    # Designations
    (
        "designations",
        [("memberId", 1), ("matchDate", -1)],
        {"name": "designations_member_date"},
    ),
    (
        "designations",
        [("refereeSection", 1), ("matchDate", -1)],
        {"name": "designations_section_date"},
    ),
    ("designations", [("matchDate", -1)], {"name": "designations_match_date"}),
    (
        "designations",
        [("memberSlug", 1), ("matchDate", -1)],
        {"name": "designations_slug_date"},
    ),
    (
        "designations",
        [("status", 1), ("matchDate", 1)],
        {"name": "designations_status_date"},
    ),
    # Members — email is sparse (many members have empty email; not globally unique)
    ("members", [("email", 1)], {"name": "members_email", "sparse": True}),
    ("members", [("meccanografico", 1)], {"name": "members_meccanografico"}),
    ("members", [("slug", 1)], {"unique": True, "name": "members_slug_unique"}),
    (
        "members",
        [("memberRole", 1), ("lastName", 1), ("firstName", 1)],
        {"name": "members_role_name"},
    ),
    # Events (schema uses `date`, not startDate; visibility via portalOnly)
    ("events", [("date", 1)], {"name": "events_date"}),
    ("events", [("portalOnly", 1), ("date", -1)], {"name": "events_portal_date"}),
    ("events", [("invitedMemberIds", 1)], {"name": "events_invited"}),
    # Other hot collections
    ("pages", [("slug", 1)], {"unique": True, "name": "pages_slug_unique"}),
    (
        "gallery_images",
        [("status", 1), ("sortOrder", 1)],
        {"name": "gallery_status_order"},
    ),
    ("gallery_images", [("memberId", 1)], {"name": "gallery_member"}),
    ("gallery_images", [("memberIds", 1)], {"name": "gallery_member_ids"}),
    (
        "presenze_evento",
        [("eventId", 1), ("memberId", 1)],
        {"unique": True, "name": "presenze_event_member"},
    ),
    (
        "messaggi_interni",
        [("chatId", 1), ("createdAt", -1)],
        {"name": "messaggi_chat_created"},
    ),
    ("comunicazioni_interne", [("createdAt", -1)], {"name": "comunicazioni_created"}),
    ("leads", [("createdAt", -1)], {"name": "leads_created"}),
    ("contact_messages", [("createdAt", -1)], {"name": "contacts_created"}),
    (
        "admin_users",
        [("email", 1)],
        {"unique": True, "name": "admin_users_email_unique"},
    ),
    (
        "admin_password_resets",
        [("tokenHash", 1)],
        {"unique": True, "name": "admin_password_resets_token_hash"},
    ),
    (
        "admin_password_resets",
        [("email", 1), ("createdAt", -1)],
        {"name": "admin_password_resets_email_created"},
    ),
]


async def create_indexes(db=None) -> int:
    """
    Ensure critical indexes exist.

    Safe to call on every startup: `create_index` is idempotent when the
    same name/keys already exist.
    """
    db = db if db is not None else get_db()
    created = 0
    for coll_name, keys, opts in INDEX_SPECS:
        coll = db[coll_name]
        try:
            await coll.create_index(keys, **opts)
            created += 1
        except Exception as exc:
            logger.warning(
                "Index %s on %s skipped: %s",
                opts.get("name"),
                coll_name,
                exc,
            )
    logger.info("Mongo indexes ensured (%s definitions)", created)
    return created


# Alias used by older call sites / docs
ensure_indexes = create_indexes
