"""Menu pubblico derivato dalle pagine CMS."""

SYSTEM_PAGE_HREFS = {
    "home": "/",
    "chi-siamo": "/chi-siamo",
    "designazioni": "/designazioni",
    "arbitri": "/arbitri",
    "osservatori": "/osservatori",
    "news": "/news",
    "eventi": "/eventi",
    "contatti": "/contatti",
    "diventa-arbitro": "/diventa-arbitro",
    "area-associati": "/area-associati/login",
}

HREF_TO_SLUG = {href: slug for slug, href in SYSTEM_PAGE_HREFS.items()}
HREF_TO_SLUG["/associati"] = "arbitri"
HREF_TO_SLUG["/associati/"] = "arbitri"

MENU_PAGE_DEFAULTS = [
    {
        "slug": "home",
        "title": "Home",
        "menuLabel": "Home",
        "menuOrder": 1,
        "showInMenu": True,
    },
    {
        "slug": "chi-siamo",
        "title": "Chi Siamo",
        "menuLabel": "Chi Siamo",
        "menuOrder": 2,
        "showInMenu": True,
    },
    {
        "slug": "designazioni",
        "title": "Designazioni",
        "menuLabel": "Designazioni",
        "menuOrder": 3,
        "showInMenu": True,
    },
    {
        "slug": "arbitri",
        "title": "Arbitri",
        "menuLabel": "Arbitri",
        "menuOrder": 4,
        "showInMenu": True,
    },
    {
        "slug": "osservatori",
        "title": "Osservatori",
        "menuLabel": "Osservatori",
        "menuOrder": 5,
        "showInMenu": True,
    },
    {
        "slug": "news",
        "title": "News & Successi",
        "menuLabel": "News & Successi",
        "menuOrder": 6,
        "showInMenu": True,
    },
    {
        "slug": "eventi",
        "title": "Eventi",
        "menuLabel": "Eventi",
        "menuOrder": 7,
        "showInMenu": True,
    },
    {
        "slug": "contatti",
        "title": "Contatti",
        "menuLabel": "Contatti",
        "menuOrder": 8,
        "showInMenu": True,
    },
    {
        "slug": "diventa-arbitro",
        "title": "Diventa Arbitro",
        "showInMenu": False,
        "menuOrder": 0,
    },
    {
        "slug": "area-associati",
        "title": "Area associati",
        "menuLabel": "Area associati",
        "showInMenu": False,
        "menuOrder": 8,
        "menuHighlight": True,
    },
    {
        "slug": "arbitro-profilo",
        "title": "Profilo arbitro",
        "showInMenu": False,
        "menuOrder": 99,
    },
]


def slug_from_href(href: str) -> str | None:
    if not href:
        return None
    if href == "/":
        return "home"
    return HREF_TO_SLUG.get(href) or HREF_TO_SLUG.get(href.rstrip("/"))


def page_href(slug: str) -> str:
    return SYSTEM_PAGE_HREFS.get(slug, f"/p/{slug}")


def page_to_nav_item(page: dict) -> dict:
    slug = page["slug"]
    return {
        "id": f"page-{slug}",
        "label": (page.get("menuLabel") or page.get("title") or slug).strip(),
        "href": page_href(slug),
        "order": page.get("menuOrder", 100),
        "enabled": True,
        "highlight": bool(page.get("menuHighlight")),
    }
