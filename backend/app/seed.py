"""One-time seed: populate MongoDB from /app/backend/seed_data/*.json + admin user.

Run on startup: idempotent (only adds if collections are empty).
"""

import os
import json
import asyncio
import logging
from datetime import datetime, timezone
from pathlib import Path
from slugify import slugify
import bcrypt

from .db import get_db
from .security import hash_password
from .sanitize import sanitize_html
from .models import (
    SiteSettings,
    Page,
    Article,
    Event,
    Official,
    Member,
    Designation,
)

logger = logging.getLogger(__name__)

SEED_DIR = Path(__file__).parent.parent / "seed_data"

# Associati demo — non re-inserire dopo cancellazione admin.
DEMO_MEMBER_SLUGS = frozenset(
    {
        "paolo-colombo",
        "giulia-ferrari",
        "martina-greco",
        "chiara-neri",
        "marco-rossi",
        "elena-sala",
        "davide-villa",
    }
)

DEMO_MEMBER_NAMES = frozenset(
    {
        "Paolo Colombo",
        "Giulia Ferrari",
        "Martina Greco",
        "Chiara Neri",
        "Marco Rossi",
        "Elena Sala",
        "Davide Villa",
    }
)


async def _seed_flag(key: str) -> bool:
    db = get_db()
    doc = (
        await db.site_settings.find_one(
            {"id": "site-settings"}, {"_id": 0, "seedFlags": 1}
        )
        or {}
    )
    return bool((doc.get("seedFlags") or {}).get(key))


async def _set_seed_flag(key: str) -> None:
    db = get_db()
    await db.site_settings.update_one(
        {"id": "site-settings"},
        {"$set": {f"seedFlags.{key}": True}},
        upsert=True,
    )


async def ensure_legacy_seed_flags() -> None:
    """DB già popolato: non rieseguire seed associati/organigramma demo."""
    db = get_db()
    if await db.members.count_documents({}) > 0:
        await _set_seed_flag("officials")
        await _set_seed_flag("associati")
        await _set_seed_flag("testimonials")


async def purge_demo_members() -> int:
    """Rimuove associati demo noti (anche se re-inseriti dal seed legacy)."""
    db = get_db()
    members = await db.members.find(
        {"slug": {"$in": list(DEMO_MEMBER_SLUGS)}},
        {"_id": 0, "id": 1},
    ).to_list(50)
    member_ids = [m["id"] for m in members]
    if member_ids:
        await db.designations.delete_many({"memberId": {"$in": member_ids}})
    await db.designations.delete_many({"memberName": {"$in": list(DEMO_MEMBER_NAMES)}})
    res = await db.members.delete_many({"slug": {"$in": list(DEMO_MEMBER_SLUGS)}})
    if res.deleted_count:
        logger.info("Rimossi %s associati demo", res.deleted_count)
    return res.deleted_count


def _now():
    return datetime.now(timezone.utc).isoformat()


def _read(name):
    with (SEED_DIR / name).open(encoding="utf-8") as f:
        return json.load(f)


# Real referee/football images (Unsplash + Pexels) for the news articles
NEWS_IMAGES = {
    "raduno-sezionale-primavera-2026": "https://images.unsplash.com/photo-1551958219-acbc608c6377?auto=format&fit=crop&w=1400&q=80",
    "promozione-francesca-conti-can-d": "https://images.unsplash.com/photo-1574629810360-7efbbe195018?auto=format&fit=crop&w=1400&q=80",
    "approfondimento-dogso-spa": "https://images.unsplash.com/photo-1543326727-cf6c39e8f84c?auto=format&fit=crop&w=1400&q=80",
    "nuovo-corso-arbitri-legnano-2026": "https://images.unsplash.com/photo-1518604666860-9ed391f76460?auto=format&fit=crop&w=1400&q=80",
    "allenamento-congiunto-polo-atletico": "https://images.unsplash.com/photo-1526676037777-05a232554f77?auto=format&fit=crop&w=1400&q=80",
    "premio-arbitro-anno-2025": "https://images.unsplash.com/photo-1517466787929-bc90951d0974?auto=format&fit=crop&w=1400&q=80",
    "focus-fuorigioco-assistenti": "https://images.unsplash.com/photo-1574629173768-7faa9f9f6f0e?auto=format&fit=crop&w=1400&q=80",
    "visita-osservatore-nazionale": "https://images.unsplash.com/photo-1577471488278-16eec37ffcc2?auto=format&fit=crop&w=1400&q=80",
    "legnano-al-memorial-regionale": "https://images.unsplash.com/photo-1551280857-2c11e3a18ad7?auto=format&fit=crop&w=1400&q=80",
}

# Skip the placeholder/junk item from original seed
SKIP_NEWS_SLUGS = {"non-so-cosa-sia"}


# Realistic, well-formatted article bodies (HTML with paragraphs/headings)
ARTICLE_BODIES = {
    "raduno-sezionale-primavera-2026": """
<p>Con grande tristezza la Sezione AIA di Legnano comunica la scomparsa dell'Arbitro Benemerito <strong>Franco Giardini</strong>, all'età di 92 anni. Un punto di riferimento storico per generazioni di associati, che hanno trovato in lui un esempio di rigore, dedizione e passione per l'arbitraggio.</p>
<h3>Una vita per l'arbitraggio</h3>
<p>Iscritto in sezione fin dagli anni Cinquanta, Franco Giardini ha arbitrato per oltre trent'anni nei campionati regionali e nazionali, raggiungendo importanti traguardi tecnici. Dopo aver appeso al chiodo il fischietto, ha continuato a vivere la sezione come Arbitro Benemerito, partecipando attivamente alla formazione dei nuovi colleghi.</p>
<h3>L'esempio per le nuove generazioni</h3>
<p>Sempre presente alle riunioni tecniche e alle attività sezionali, è stato per molti aspiranti arbitri un mentore e una guida. La sua eredità rimane nelle storie che ci ha raccontato, nelle decisioni difficili che ha saputo prendere e nello spirito associativo che ha sempre incarnato.</p>
<blockquote>"Un fischietto non si dimentica mai. Si tramanda, come ogni cosa importante." — Franco Giardini</blockquote>
<p>Il Consiglio Direttivo Sezionale, gli associati tutti e gli organi tecnici si stringono attorno alla famiglia in questo momento di dolore.</p>
""",
    "promozione-francesca-conti-can-d": """
<p>Un traguardo importante per una giovane associata cresciuta nella nostra sezione. <strong>Francesca Conti</strong> ha ottenuto la promozione nel ruolo nazionale dopo una stagione di grande continuità tecnica e atletica.</p>
<h3>Il percorso</h3>
<p>Iscritta alla Sezione AIA di Legnano dal 2016, Francesca ha attraversato tutte le categorie del calcio dilettantistico, distinguendosi per personalità in campo, gestione dei calciatori e accurata applicazione del regolamento. Negli ultimi due anni ha arbitrato gare di alto livello regionale, ricevendo valutazioni costantemente positive.</p>
<h3>I complimenti della sezione</h3>
<p>Il Consiglio Direttivo Sezionale le ha rivolto i propri complimenti per l'impegno, la serietà e la capacità di rappresentare Legnano sui campi di tutta Italia. Un esempio per le ragazze e i ragazzi che si avvicinano al corso arbitri e che possono trovare nel suo percorso una concreta fonte di ispirazione.</p>
<p>A Francesca, da parte di tutti gli associati, un grosso in bocca al lupo per le sfide della nuova categoria.</p>
""",
    "approfondimento-dogso-spa": """
<p>La riunione tecnica obbligatoria di questa settimana ha affrontato un tema sempre attuale e delicato: la distinzione fra <strong>SPA</strong> (Stopping a Promising Attack) e <strong>DOGSO</strong> (Denying an Obvious Goal-Scoring Opportunity).</p>
<h3>I quattro criteri DOGSO</h3>
<p>Per identificare correttamente la chiara occasione da rete, l'arbitro deve valutare contemporaneamente quattro elementi:</p>
<ul>
<li><strong>Distanza dalla porta</strong>: tanto più vicina, tanto più probabile la DOGSO;</li>
<li><strong>Direzione generale dell'azione</strong>: verso la porta avversaria;</li>
<li><strong>Controllo del pallone</strong>: possibilità concreta di mantenere il possesso;</li>
<li><strong>Numero e posizione dei difendenti</strong>: nessun difensore in grado di intervenire prima della conclusione.</li>
</ul>
<h3>Il lavoro in aula</h3>
<p>Gli associati hanno analizzato dieci clip reali tratte dai campionati professionistici e dilettantistici, esercitandosi a riconoscere i criteri e a calibrare correttamente i provvedimenti disciplinari. È stato dedicato spazio anche alla gestione della comunicazione con i calciatori dopo l'adozione della sanzione.</p>
<p>Particolare attenzione è stata riservata alle situazioni di confine, dove la lettura della direzione dell'azione può modificare in modo determinante la qualificazione dell'episodio.</p>
""",
    "nuovo-corso-arbitri-legnano-2026": """
<p>Sono ufficialmente aperte le preiscrizioni al nuovo <strong>corso arbitri</strong> della Sezione AIA di Legnano. Il percorso formativo, completamente <strong>gratuito</strong>, è rivolto a ragazze e ragazzi dai 15 anni in su che vogliono vivere il calcio da protagonisti.</p>
<h3>Il programma del corso</h3>
<p>Le lezioni alterneranno teoria e pratica, con un calendario pensato per essere compatibile con scuola e lavoro. Affronteremo:</p>
<ul>
<li>Regolamento del Gioco del Calcio e delle Norme di Funzionamento</li>
<li>Analisi video di episodi reali</li>
<li>Preparazione atletica specifica</li>
<li>Testimonianze di associati esperti e arbitri di categorie superiori</li>
<li>Esercitazioni in campo</li>
</ul>
<h3>Vantaggi per chi diventa arbitro</h3>
<p>Oltre alla passione per il calcio, gli associati ricevono il kit ufficiale, un rimborso per ogni gara diretta e l'opportunità di una crescita personale unica: leadership, gestione dello stress, decisione sotto pressione.</p>
<p>Le lezioni iniziano in autunno presso la sede sezionale. Al termine del percorso è previsto l'esame di abilitazione, che apre la strada alla prima stagione effettiva sui campi.</p>
""",
    "allenamento-congiunto-polo-atletico": """
<p>Gli associati della Sezione AIA di Legnano hanno partecipato a una seduta tecnica e atletica congiunta presso il polo sezionale, guidati dal Referente Atletico e dagli organi tecnici.</p>
<h3>Programma della seduta</h3>
<p>Il riscaldamento ha previsto esercizi di mobilità articolare e attivazione muscolare, fondamentali per prevenire infortuni. Si è poi passati al <strong>test intermittente</strong>, sezione centrale dell'allenamento dell'arbitro moderno, con lavoro mirato sulla resistenza specifica.</p>
<p>La parte finale è stata dedicata alla rapidità e ai cambi di direzione, simulando spostamenti tipici della gara per migliorare posizionamento, lettura dell'azione e reattività.</p>
<h3>Il valore del gruppo</h3>
<p>Allenarsi insieme rafforza lo spirito di squadra di una categoria che vive il proprio sport in modo apparentemente solitario, ma che trae forza dal collettivo. Le occasioni come questa sono pilastri della vita sezionale.</p>
""",
    "premio-arbitro-anno-2025": """
<p>Durante la cena sezionale di fine stagione è stato consegnato il <strong>Premio Arbitro dell'Anno</strong> a <strong>Matteo Colombo</strong>, riconoscimento che la Sezione AIA di Legnano assegna ogni anno a chi più si è distinto sui campi e nella vita associativa.</p>
<h3>Una stagione esemplare</h3>
<p>Matteo Colombo ha arbitrato in Eccellenza con valutazioni eccellenti, dimostrando crescita tecnica, gestione personalità e disponibilità verso i colleghi più giovani. Ha inoltre partecipato attivamente a tutte le riunioni tecniche e agli allenamenti collettivi.</p>
<h3>Il valore del riconoscimento</h3>
<p>Il premio non celebra solo la prestazione tecnica, ma anche lo spirito di servizio: presenza in sezione, supporto ai colleghi alle prime esperienze, contributo alla vita associativa. Caratteristiche che fanno di un buon arbitro un grande associato.</p>
<p>Complimenti a Matteo da parte di tutti gli associati e del Consiglio Direttivo.</p>
""",
    "focus-fuorigioco-assistenti": """
<p>La commissione tecnica ha proposto una serata di approfondimento dedicata agli <strong>assistenti arbitrali</strong>, figura cardine nella precisione delle decisioni più delicate della gara.</p>
<h3>I temi affrontati</h3>
<p>Si è lavorato su tre aree fondamentali:</p>
<ul>
<li><strong>Allineamento</strong>: corretto posizionamento con il penultimo difendente o con il pallone, a seconda della situazione;</li>
<li><strong>Concentrazione</strong>: gestione dei micro-momenti che precedono il fuorigioco, con la mente sempre sull'episodio;</li>
<li><strong>Wait and see</strong>: l'arte di attendere il momento giusto per segnalare, soprattutto in zona offensiva.</li>
</ul>
<h3>La collaborazione con l'arbitro</h3>
<p>Particolare spazio è stato dedicato alle segnalazioni nei pressi dell'area di rigore, dove la comunicazione tra arbitro e assistente fa la differenza tra una decisione corretta e un errore che pesa sull'intera gara.</p>
""",
    "visita-osservatore-nazionale": """
<p>La Sezione AIA di Legnano ha avuto il piacere di accogliere un <strong>Osservatore Nazionale</strong> per una riunione tecnica ricca di spunti e contenuti di alto livello.</p>
<h3>Personalità, credibilità, comunicazione</h3>
<p>Al centro dell'incontro la costruzione della <strong>credibilità arbitrale</strong>: come si guadagna sul campo, come si mantiene partita dopo partita, come si ricostruisce dopo un errore. Sono stati analizzati casi concreti di gestione delle situazioni più delicate: rigori, espulsioni, gestione delle proteste.</p>
<h3>La postura comunicativa</h3>
<p>Non solo gesti tecnici: la postura, lo sguardo, il tono della voce. Tutto comunica all'arbitro chi siamo e quanto controllo abbiamo della partita. Esercitazioni pratiche hanno permesso agli associati di sperimentare diverse soluzioni in situazioni di pressione.</p>
""",
    "legnano-al-memorial-regionale": """
<p>La rappresentativa sezionale ha preso parte al <strong>memorial regionale</strong> tra le sezioni AIA della Lombardia, distinguendosi per fair play, organizzazione e spirito di gruppo.</p>
<h3>Risultati sul campo</h3>
<p>I nostri associati hanno disputato un'ottima manifestazione, raggiungendo le fasi finali del torneo. Al di là dei risultati, il valore aggiunto è stato l'occasione di confronto con colleghi di altre sezioni: tecniche di arbitraggio, gestione della preparazione atletica, organizzazione associativa.</p>
<h3>Una giornata di sezione</h3>
<p>Erano presenti anche associati non in campo, dirigenti e familiari, a sottolineare quanto questi momenti rappresentino la vera anima della vita sezionale. Un ringraziamento agli organizzatori e ai partecipanti.</p>
""",
}


async def seed_admin():
    db = get_db()
    email = (os.environ.get("ADMIN_EMAIL") or "legnano@aia-figc.it").strip().lower()
    password = (os.environ.get("ADMIN_PASSWORD") or "").strip()
    if not password:
        raise RuntimeError(
            "ADMIN_PASSWORD non configurato. Impostalo in backend/.env "
            "(vedi backend/.env.example) oppure in .env per docker compose."
        )
    name = os.environ.get("ADMIN_NAME", "Amministratore")
    pwd_hash = hash_password(password)
    force_pwd = os.environ.get("ADMIN_PASSWORD_FORCE_SYNC", "").strip().lower() in (
        "1",
        "true",
        "yes",
    )

    root = await db.admin_users.find_one({"id": "admin-root"}, {"_id": 0})
    if root:
        old_email = (root.get("email") or "").strip().lower()
        updates: dict = {"email": email, "name": name}
        if force_pwd or not root.get("passwordHash"):
            updates["passwordHash"] = pwd_hash
        await db.admin_users.update_one({"id": "admin-root"}, {"$set": updates})
        if old_email and old_email != email:
            await db.admin_users.delete_many(
                {"email": old_email, "id": {"$ne": "admin-root"}}
            )
        return

    existing = await db.admin_users.find_one({"email": email}, {"_id": 0})
    if existing:
        updates = {"name": name}
        if force_pwd or not existing.get("passwordHash"):
            updates["passwordHash"] = pwd_hash
        await db.admin_users.update_one({"email": email}, {"$set": updates})
        return
    await db.admin_users.insert_one(
        {
            "id": "admin-root",
            "email": email,
            "passwordHash": pwd_hash,
            "name": name,
            "createdAt": _now(),
        }
    )


async def seed_settings():
    db = get_db()
    if await db.site_settings.count_documents({}) > 0:
        return
    s = SiteSettings()
    doc = s.model_dump()
    doc["id"] = "site-settings"
    await db.site_settings.insert_one(doc.copy())


def _content_to_body_html(content: str) -> str:
    if not (content or "").strip():
        return ""
    paras = [x.strip() for x in content.split("\n") if x.strip()]
    return "\n".join(f"<p>{x}</p>" for x in paras)


def _system_page_catalog():
    catalog = {p["slug"]: p for p in _read("pages.json")}
    catalog["area-associati"] = {
        "slug": "area-associati",
        "title": "Area associati",
        "heading": "Area associati",
        "summary": "Accesso riservato agli arbitri associati della sezione.",
        "status": "published",
        "showInMenu": False,
        "menuLabel": "Area associati",
    }
    catalog["arbitro-profilo"] = {
        "slug": "arbitro-profilo",
        "title": "Profilo arbitro",
        "heading": "Profilo arbitro",
        "summary": "Layout della pagina pubblica /arbitri/nome-cognome.",
        "status": "published",
        "showInMenu": False,
        "menuLabel": "",
    }
    return catalog


async def _migrate_nav_items_to_pages(db):
    """Migrazione una tantum dal vecchio menu nav_items."""
    from .page_nav import MENU_PAGE_DEFAULTS, slug_from_href

    settings = await db.site_settings.find_one(
        {"id": "site-settings"}, {"_navMenuMigrated": 1}
    )
    if settings and settings.get("_navMenuMigrated"):
        return
    defaults_by_slug = {d["slug"]: d for d in MENU_PAGE_DEFAULTS}
    nav_items = await db.nav_items.find({}).sort("order", 1).to_list(100)
    for it in nav_items:
        if not it.get("enabled", True):
            continue
        slug = slug_from_href(it.get("href") or "")
        if not slug:
            continue
        patch = {
            "showInMenu": True,
            "menuLabel": (it.get("label") or "").strip(),
            "menuOrder": it.get("order", 100),
            "menuHighlight": bool(it.get("highlight")),
        }
        existing = await db.pages.find_one({"slug": slug}, {"_id": 0, "id": 1})
        if existing:
            await db.pages.update_one({"slug": slug}, {"$set": patch})
        else:
            d = defaults_by_slug.get(slug, {})
            page = Page(
                slug=slug,
                title=d.get("title") or patch["menuLabel"] or slug,
                template="system",
                status="published",
                showInMenu=patch["showInMenu"],
                menuLabel=patch["menuLabel"],
                menuOrder=patch["menuOrder"],
                menuHighlight=patch["menuHighlight"],
            )
            await db.pages.insert_one(page.model_dump().copy())
    await db.site_settings.update_one(
        {"id": "site-settings"},
        {"$set": {"_navMenuMigrated": True}},
        upsert=True,
    )


async def ensure_all_system_pages():
    """Crea/aggiorna tutte le pagine di sistema (idempotente)."""
    from .page_nav import MENU_PAGE_DEFAULTS

    db = get_db()
    await _migrate_nav_items_to_pages(db)

    menu_by_slug = {d["slug"]: d for d in MENU_PAGE_DEFAULTS}
    catalog = _system_page_catalog()
    block_slugs = {"home", "diventa-arbitro"}
    patch_fields = (
        "title",
        "status",
        "eyebrow",
        "heading",
        "summary",
        "image",
        "menuLabel",
        "menuOrder",
        "showInMenu",
        "menuHighlight",
        "metaTitle",
        "metaDescription",
    )

    created = 0
    updated = 0

    for slug, src in catalog.items():
        if slug in block_slugs:
            continue

        menu = menu_by_slug.get(slug, {})
        title = src.get("title") or menu.get("title") or slug
        body_html = sanitize_html(_content_to_body_html(src.get("content") or ""))
        doc = {
            "slug": slug,
            "title": title,
            "template": "system",
            "status": src.get("status", "published"),
            "eyebrow": src.get("eyebrow", ""),
            "heading": src.get("heading") or title,
            "summary": src.get("summary", ""),
            "image": src.get("image", ""),
            "bodyHtml": body_html,
            "blocks": [],
            "showInMenu": menu.get("showInMenu", bool(src.get("showInMenu"))),
            "menuLabel": menu.get("menuLabel") or src.get("menuLabel", ""),
            "menuOrder": menu.get("menuOrder", src.get("menuOrder", 100)),
            "menuHighlight": menu.get("menuHighlight", False),
            "metaTitle": f"{title} · AIA Legnano",
            "metaDescription": src.get("summary", ""),
        }

        existing = await db.pages.find_one({"slug": slug}, {"_id": 0})
        if not existing:
            await db.pages.insert_one(Page(**doc).model_dump().copy())
            created += 1
            logger.info("Pagina sistema creata: %s", slug)
            continue

        patch = {"template": "system"}
        for key in patch_fields:
            new_val = doc.get(key)
            old_val = existing.get(key)
            if key in ("showInMenu", "menuHighlight"):
                if old_val is None:
                    patch[key] = new_val
                continue
            if key == "menuOrder":
                if old_val is None or old_val == 100:
                    patch[key] = new_val
                continue
            if isinstance(new_val, str):
                if not (old_val or "").strip() and new_val.strip():
                    patch[key] = new_val
            elif old_val is None and new_val is not None:
                patch[key] = new_val

        if not (existing.get("bodyHtml") or "").strip() and body_html:
            patch["bodyHtml"] = body_html

        if len(patch) > 1 or (len(patch) == 1 and "template" not in patch):
            await db.pages.update_one({"slug": slug}, {"$set": patch})
            updated += 1

    for slug in block_slugs:
        menu = menu_by_slug.get(slug, {})
        src = catalog.get(slug, {})
        existing = await db.pages.find_one({"slug": slug}, {"_id": 0})
        if not existing:
            continue
        title = src.get("title") or existing.get("title") or slug
        patch = {}
        if existing.get("template") != "system":
            patch["template"] = "system"
        for key in patch_fields:
            new_val = (
                menu.get(key)
                if key in ("menuLabel", "menuOrder", "showInMenu", "menuHighlight")
                and menu.get(key) is not None
                else src.get(key) if key in src else None
            )
            if key == "metaTitle" and not new_val:
                new_val = f"{title} · AIA Legnano"
            if key == "metaDescription" and not new_val:
                new_val = src.get("summary", "")
            if key == "heading" and not new_val:
                new_val = src.get("heading") or title
            old_val = existing.get(key)
            if key in ("showInMenu", "menuHighlight"):
                if old_val is None and new_val is not None:
                    patch[key] = new_val
            elif key == "menuOrder":
                if (old_val is None or old_val == 100) and new_val is not None:
                    patch[key] = new_val
            elif (
                isinstance(new_val, str)
                and new_val.strip()
                and not (old_val or "").strip()
            ):
                patch[key] = new_val
        if patch:
            await db.pages.update_one({"slug": slug}, {"$set": patch})
            updated += 1

    for menu in MENU_PAGE_DEFAULTS:
        slug = menu["slug"]
        if slug in catalog or slug in block_slugs:
            continue
        if await db.pages.find_one({"slug": slug}, {"_id": 0, "id": 1}):
            continue
        await db.pages.insert_one(
            Page(
                slug=slug,
                title=menu.get("title", slug),
                template="system",
                status="published",
                showInMenu=menu.get("showInMenu", False),
                menuLabel=menu.get("menuLabel", ""),
                menuOrder=menu.get("menuOrder", 100),
                menuHighlight=menu.get("menuHighlight", False),
            )
            .model_dump()
            .copy()
        )
        created += 1
        logger.info("Pagina sistema creata: %s", slug)

    if created or updated:
        logger.info("Pagine sistema: %s create, %s aggiornate", created, updated)

    await remove_risorse_page(db)
    await ensure_osservatori_page(db)
    await ensure_home_hero_no_secondary_cta(db)
    blocks_seeded = await ensure_system_page_blocks(db)
    logos_fixed = await ensure_section_logo_in_blocks(db)
    return {
        "created": created,
        "updated": updated,
        "blocksSeeded": blocks_seeded,
        "logosFixed": logos_fixed,
    }


SECTION_LOGO_URL = "/brand/logo-aia-legnano.png"
NATIONAL_LOGO_URL = "/brand/logo-aia-figc.png"


async def ensure_section_logo_in_blocks(db=None):
    """Sostituisce il logo AIA nazionale con quello sezionale nei blocchi CMS."""
    if db is None:
        db = get_db()
    fixed = 0
    pages = await db.pages.find(
        {"blocks.0": {"$exists": True}}, {"_id": 0, "slug": 1, "blocks": 1}
    ).to_list(200)
    for page in pages:
        blocks = page.get("blocks") or []
        changed = False
        for block in blocks:
            cfg = block.get("config")
            if not isinstance(cfg, dict):
                continue
            if cfg.get("badgeLogoUrl") == NATIONAL_LOGO_URL:
                cfg["badgeLogoUrl"] = SECTION_LOGO_URL
                changed = True
        if changed:
            await db.pages.update_one(
                {"slug": page["slug"]}, {"$set": {"blocks": blocks}}
            )
            fixed += 1
            logger.info("Logo sezionale: %s", page["slug"])
    if fixed:
        logger.info("Logo sezionale applicato a %s pagine CMS", fixed)
    return fixed


async def remove_risorse_page(db=None):
    """Rimuove la pagina Risorse (dismessa)."""
    if db is None:
        db = get_db()
    res = await db.pages.delete_one({"slug": "risorse"})
    if res.deleted_count:
        logger.info("Pagina rimossa: risorse")
    return res.deleted_count


async def ensure_compact_page_headers(db=None):
    """Intestazione compatta: copia testi dal blocco Hero ai campi pagina e rimuove l'hero."""
    from .system_page_blocks import COMPACT_HEADER_SLUGS

    if db is None:
        db = get_db()
    fixed = 0
    for slug in COMPACT_HEADER_SLUGS:
        page = await db.pages.find_one({"slug": slug}, {"_id": 0})
        if not page:
            continue
        blocks = page.get("blocks") or []
        if not blocks or blocks[0].get("type") != "hero":
            continue
        hero = blocks[0].get("config") or {}
        patch = {"blocks": blocks[1:]}
        if hero.get("eyebrow"):
            patch["eyebrow"] = hero["eyebrow"]
        if hero.get("title"):
            patch["heading"] = hero["title"]
        if hero.get("subtitle"):
            patch["summary"] = hero["subtitle"]
        if hero.get("backgroundImage"):
            patch["image"] = hero["backgroundImage"]
        await db.pages.update_one({"slug": slug}, {"$set": patch})
        fixed += 1
        logger.info("Intestazione compatta: %s", slug)
    return fixed


async def ensure_fixed_layout_pages(db=None):
    """Login e profilo arbitro: nessun blocco CMS."""
    from .system_page_blocks import FIXED_LAYOUT_SLUGS

    if db is None:
        db = get_db()
    for slug in FIXED_LAYOUT_SLUGS:
        await db.pages.update_one({"slug": slug}, {"$set": {"blocks": []}})
    return len(FIXED_LAYOUT_SLUGS)


async def ensure_system_page_blocks(db=None):
    """Applica blocchi predefiniti alle pagine di sistema ancora vuote."""
    from .system_page_blocks import FIXED_LAYOUT_SLUGS, default_blocks_for_slug
    from .blocks_sanitize import sanitize_blocks

    if db is None:
        db = get_db()

    await ensure_compact_page_headers(db)
    await ensure_fixed_layout_pages(db)

    seeded = 0
    pages = await db.pages.find({"template": "system"}, {"_id": 0}).to_list(100)
    block_pages = {sp["slug"]: sp.get("blocks") or [] for sp in build_system_pages()}

    for page in pages:
        slug = page.get("slug") or ""
        if slug in FIXED_LAYOUT_SLUGS:
            continue
        if page.get("blocks"):
            continue
        blocks = block_pages.get(slug) or default_blocks_for_slug(slug, page)
        if not blocks:
            continue
        await db.pages.update_one(
            {"slug": slug},
            {"$set": {"blocks": sanitize_blocks(blocks)}},
        )
        seeded += 1
        logger.info("Blocchi predefiniti: %s (%s blocchi)", slug, len(blocks))

    if seeded:
        logger.info("Blocchi CMS: %s pagine aggiornate", seeded)
    return seeded


def suggested_page_content(slug: str, page: dict | None = None) -> dict:
    """Blocchi e campi intestazione suggeriti per il ripristino da admin."""
    from .system_page_blocks import (
        COMPACT_HEADER_SLUGS,
        FIXED_LAYOUT_SLUGS,
        default_blocks_for_slug,
    )
    from .blocks_sanitize import sanitize_blocks

    if slug in FIXED_LAYOUT_SLUGS:
        return {"blocks": []}
    page = page or {}
    block_pages = {sp["slug"]: sp for sp in build_system_pages()}
    sp = block_pages.get(slug)
    blocks = (sp.get("blocks") if sp else None) or default_blocks_for_slug(slug, page)
    out: dict = {"blocks": sanitize_blocks(blocks)}
    if sp:
        for key in ("eyebrow", "heading", "summary", "image"):
            if key in sp:
                out[key] = sp[key]
    elif slug in COMPACT_HEADER_SLUGS:
        cat = _system_page_catalog().get(slug, {})
        out["eyebrow"] = cat.get("eyebrow", "")
        out["heading"] = cat.get("heading") or cat.get("title", "")
        out["summary"] = cat.get("summary", "")
        out["image"] = ""
    return out


async def reset_page_blocks(slug: str, page: dict | None = None) -> list:
    """Ripristina i blocchi suggeriti per una pagina (sovrascrive)."""
    return suggested_page_content(slug, page).get("blocks") or []


async def ensure_article_categories_seed():
    """Inizializza categorie articoli su DB esistenti."""
    from .article_categories import ensure_article_categories_seed as _ensure

    db = get_db()
    await _ensure(db)


async def ensure_event_types_seed():
    """Inizializza tipi evento su DB esistenti."""
    from .event_categories import ensure_event_types_seed as _ensure

    db = get_db()
    await _ensure(db)


def _article_mentions_raduni(article: dict) -> bool:
    haystack = " ".join(
        [
            article.get("title") or "",
            article.get("excerpt") or "",
            article.get("bodyHtml") or "",
            article.get("slug") or "",
        ]
    ).lower()
    return "radun" in haystack


async def ensure_raduni_article_categories(db=None) -> int:
    """Articoli che citano raduni → categoria Raduni."""
    from .article_categories import ensure_category_exists

    if db is None:
        db = get_db()
    await ensure_category_exists(db, "Raduni")
    ts = datetime.now(timezone.utc).isoformat()
    updated = 0
    articles = await db.articles.find({}, {"_id": 0}).to_list(5000)
    for art in articles:
        if not _article_mentions_raduni(art):
            continue
        if (art.get("category") or "").strip().casefold() == "raduni":
            continue
        await db.articles.update_one(
            {"id": art["id"]},
            {"$set": {"category": "Raduni", "updatedAt": ts}},
        )
        await db.gallery_images.update_many(
            {"articleId": art["id"]},
            {"$set": {"category": "Raduni", "updatedAt": ts}},
        )
        updated += 1
    if updated:
        logger.info("Categoria Raduni: aggiornati %s articoli", updated)
    return updated


async def ensure_chi_siamo_story_block_layout():
    """Chi siamo: titolo solo nel banner navy; il blocco storia senza titolo duplicato."""
    db = get_db()
    page = await db.pages.find_one({"slug": "chi-siamo"}, {"_id": 0, "blocks": 1})
    if not page:
        return 0
    blocks = page.get("blocks") or []
    changed = False
    for block in blocks:
        if block.get("type") != "rich_text":
            continue
        cfg = dict(block.get("config") or {})
        if (cfg.get("eyebrow") or "").strip() or (cfg.get("title") or "").strip():
            cfg["eyebrow"] = ""
            cfg["title"] = ""
            block["config"] = cfg
            changed = True
        break
    if changed:
        await db.pages.update_one({"slug": "chi-siamo"}, {"$set": {"blocks": blocks}})
        logger.info("Chi siamo: rimosso titolo duplicato dal blocco storia")
    return 1 if changed else 0


async def ensure_chi_siamo_content():
    """Testo iniziale Chi siamo — solo se la pagina non ha ancora contenuto."""
    from .chi_siamo_content import CHI_SIAMO_BODY_HTML, CHI_SIAMO_SUMMARY
    from .sanitize import sanitize_html

    db = get_db()
    settings = await db.site_settings.find_one(
        {"id": "site-settings"}, {"_chiSiamoSeeded": 1}
    )
    if settings and settings.get("_chiSiamoSeeded"):
        return
    existing = await db.pages.find_one(
        {"slug": "chi-siamo"}, {"bodyHtml": 1, "blocks": 1}
    )
    if existing and (
        (existing.get("bodyHtml") or "").strip() or existing.get("blocks")
    ):
        await db.site_settings.update_one(
            {"id": "site-settings"},
            {"$set": {"_chiSiamoSeeded": True}},
            upsert=True,
        )
        return
    body = sanitize_html(CHI_SIAMO_BODY_HTML)
    await db.pages.update_one(
        {"slug": "chi-siamo"},
        {
            "$set": {
                "bodyHtml": body,
                "summary": CHI_SIAMO_SUMMARY,
                "heading": "Chi siamo",
                "eyebrow": "Identità sezionale",
                "image": "",
            }
        },
        upsert=False,
    )
    await db.site_settings.update_one(
        {"id": "site-settings"},
        {"$set": {"_chiSiamoSeeded": True}},
        upsert=True,
    )


async def ensure_home_hero_no_secondary_cta(db=None):
    """Rimuove la CTA secondaria dall'hero della home (es. link Risorse)."""
    if db is None:
        db = get_db()
    page = await db.pages.find_one({"slug": "home"}, {"_id": 0, "blocks": 1})
    if not page:
        return 0
    blocks = page.get("blocks") or []
    changed = False
    for block in blocks:
        if block.get("type") != "hero":
            continue
        cfg = dict(block.get("config") or {})
        sec = cfg.get("secondaryCta") or {}
        label = (sec.get("label") or "").strip()
        href = (sec.get("href") or "").strip()
        if not label and not href:
            continue
        if href == "/risorse" or "risors" in label.lower() or label or href:
            cfg["secondaryCta"] = {"label": "", "href": ""}
            block["config"] = cfg
            changed = True
    if changed:
        await db.pages.update_one({"slug": "home"}, {"$set": {"blocks": blocks}})
        logger.info("Home: rimossa CTA secondaria hero")
    await db.pages.update_one(
        {"slug": "home"},
        {"$set": {"secondaryCtaLabel": "", "secondaryCtaHref": ""}},
    )
    return 1 if changed else 0


async def ensure_home_events_limit():
    """Home: massimo 3 prossimi eventi nel blocco events_list + widget Instagram."""
    db = get_db()
    page = await db.pages.find_one({"slug": "home"}, {"_id": 0, "blocks": 1})
    if not page:
        return
    blocks = page.get("blocks") or []
    changed = False
    for block in blocks:
        if block.get("type") != "events_list":
            continue
        cfg = dict(block.get("config") or {})
        if cfg.get("limit") != 3:
            cfg["limit"] = 3
            changed = True
        if cfg.get("showInstagramWidget") is False:
            cfg["showInstagramWidget"] = True
            changed = True
        if cfg.get("showCalendar") is True:
            cfg["showCalendar"] = False
            changed = True
        block["config"] = cfg
    if changed:
        await db.pages.update_one({"slug": "home"}, {"$set": {"blocks": blocks}})


async def ensure_eventi_list_layout():
    """Pagina /eventi: elenco (3 prossimi) + calendario affiancato."""
    db = get_db()
    page = await db.pages.find_one({"slug": "eventi"}, {"_id": 0, "blocks": 1})
    if not page:
        return 0
    blocks = page.get("blocks") or []
    changed = False
    desired = {
        "eyebrow": "Calendario sezionale",
        "title": "Prossimi eventi",
        "limit": 3,
        "upcomingOnly": True,
        "ctaLabel": "",
        "ctaHref": "/eventi",
        "showInstagramWidget": False,
        "showPresidentCard": False,
        "showCalendar": True,
    }
    if not blocks:
        from .system_page_blocks import default_blocks_for_slug
        from .blocks_sanitize import sanitize_blocks

        new_blocks = sanitize_blocks(default_blocks_for_slug("eventi", page))
        await db.pages.update_one({"slug": "eventi"}, {"$set": {"blocks": new_blocks}})
        logger.info("Eventi: layout lista + calendario applicato")
        return 1
    for block in blocks:
        if block.get("type") != "events_list":
            continue
        cfg = dict(block.get("config") or {})
        for key, val in desired.items():
            if cfg.get(key) != val:
                cfg[key] = val
                changed = True
        block["config"] = cfg
    if changed:
        await db.pages.update_one({"slug": "eventi"}, {"$set": {"blocks": blocks}})
        logger.info("Eventi: aggiornato blocco events_list (calendario + 3 eventi)")
        return 1
    return 0


async def ensure_diventa_arbitro_text_image_aspect():
    """Diventa Arbitro: cornice immagine «Corso gratuito» verticale 3:4."""
    db = get_db()
    page = await db.pages.find_one({"slug": "diventa-arbitro"}, {"_id": 0, "blocks": 1})
    if not page:
        return
    blocks = page.get("blocks") or []
    changed = False
    for block in blocks:
        if block.get("type") != "text_image":
            continue
        cfg = block.setdefault("config", {})
        if cfg.get("imageAspect") != "3:4":
            cfg["imageAspect"] = "3:4"
            changed = True
    if changed:
        await db.pages.update_one(
            {"slug": "diventa-arbitro"}, {"$set": {"blocks": blocks}}
        )


async def ensure_compact_header_pages(db=None):
    """Pagine a banner navy: campi intestazione compilati e senza blocchi Hero."""
    from .system_page_blocks import COMPACT_HEADER_SLUGS

    if db is None:
        db = get_db()
    catalog = _system_page_catalog()
    fixed = 0
    for slug in COMPACT_HEADER_SLUGS:
        page = await db.pages.find_one({"slug": slug}, {"_id": 0})
        if not page:
            continue
        src = catalog.get(slug, {})
        patch: dict = {}
        for key, src_key in (
            ("eyebrow", "eyebrow"),
            ("heading", "heading"),
            ("summary", "summary"),
        ):
            if not (page.get(key) or "").strip():
                val = (src.get(src_key) or "").strip()
                if key == "heading" and not val:
                    val = (src.get("title") or page.get("title") or "").strip()
                if val:
                    patch[key] = val
        if (page.get("image") or "").strip():
            patch["image"] = ""
        blocks = page.get("blocks") or []
        without_hero = [b for b in blocks if b.get("type") != "hero"]
        if len(without_hero) != len(blocks):
            patch["blocks"] = without_hero
        if patch:
            await db.pages.update_one({"slug": slug}, {"$set": patch})
            fixed += 1
            logger.info("Banner compatto: %s", slug)
    return fixed


HOME_CORSO_ARBITRI_IMAGE = "/images/home-corso-arbitri.png"


async def ensure_home_corso_arbitri_cta_image():
    """Home: foto arbitri nel banner «Corso Arbitri · Iscrizioni aperte»."""
    db = get_db()
    page = await db.pages.find_one({"slug": "home"}, {"_id": 0, "blocks": 1})
    if not page:
        return
    blocks = page.get("blocks") or []
    changed = False
    for block in blocks:
        if block.get("type") != "cta":
            continue
        cfg = block.setdefault("config", {})
        eyebrow = (cfg.get("eyebrow") or "").lower()
        if "corso arbitri" not in eyebrow:
            continue
        if cfg.get("backgroundImage") != HOME_CORSO_ARBITRI_IMAGE:
            cfg["backgroundImage"] = HOME_CORSO_ARBITRI_IMAGE
            cfg["backgroundImageSource"] = HOME_CORSO_ARBITRI_IMAGE
            changed = True
    if changed:
        await db.pages.update_one({"slug": "home"}, {"$set": {"blocks": blocks}})
        logger.info("Home: aggiornata immagine CTA corso arbitri")


async def ensure_diventa_arbitro_testimonials():
    """Diventa Arbitro: blocco testimonianze prima del form di preiscrizione."""
    db = get_db()
    page = await db.pages.find_one({"slug": "diventa-arbitro"}, {"_id": 0, "blocks": 1})
    if not page:
        return
    blocks = page.get("blocks") or []
    if any(b.get("type") == "testimonials" for b in blocks):
        return
    testimonials = _block(
        "testimonials",
        {
            "eyebrow": "Voci dalla sezione",
            "title": "Cosa dicono gli arbitri",
            "useGlobal": True,
            "items": [],
        },
    )
    insert_at = len(blocks)
    for i, block in enumerate(blocks):
        if block.get("type") == "cta":
            insert_at = i
            break
    blocks.insert(insert_at, testimonials)
    await db.pages.update_one({"slug": "diventa-arbitro"}, {"$set": {"blocks": blocks}})


async def seed_pages():
    db = get_db()
    # Convert original simple pages into modern block-based system pages
    system_pages = build_system_pages()
    for sp in system_pages:
        existing = await db.pages.find_one(
            {"slug": sp["slug"]}, {"_id": 0, "blocks": 1, "template": 1}
        )
        if existing and existing.get("blocks"):
            # already seeded with blocks - keep admin edits
            continue
        if existing:
            await db.pages.update_one({"slug": sp["slug"]}, {"$set": sp})
        else:
            await db.pages.insert_one(sp.copy())
    # Altre pagine di sistema (designazioni, news, arbitri, …) → ensure_all_system_pages()


def _block(t, cfg, enabled=True):
    return {
        "id": str(__import__("uuid").uuid4()),
        "type": t,
        "config": cfg,
        "enabled": enabled,
    }


def _diventa_arbitro_block_configs():
    """Testi allineati al portale nazionale AIA FIGC (struttura blocchi invariata)."""
    return {
        "hero": {
            "eyebrow": "Corso Arbitri · Iscrizioni Aperte",
            "title": "Diventa Arbitro di Calcio",
            "subtitle": (
                "Vivi il calcio da protagonista! Partecipa al corso gratuito per arbitri "
                "e inizia un'esperienza unica con la Sezione AIA di Legnano."
            ),
            "overlay": "navy",
            "height": "medium",
            "primaryCta": {"label": "Iscriviti ora", "href": "#form"},
        },
        "text_image": {
            "eyebrow": "L'AIA ti aspetta",
            "title": "Entra nella grande famiglia degli arbitri italiani",
            "html": (
                "<p>L'Associazione Italiana Arbitri (AIA) è l'organizzazione che dal 1911 riunisce, "
                "all'interno della Federazione Italiana Giuoco Calcio, tutti gli arbitri italiani. "
                "Entrare a far parte di questa grande famiglia significa vivere il calcio da una "
                "prospettiva unica e privilegiata.</p>"
                "<p>Diventare arbitro non vuol dire solo dirigere partite: significa crescere come persona, "
                "sviluppare capacità decisionali, acquisire sicurezza e autorevolezza, imparare a gestire "
                "situazioni complesse e fare nuove amicizie.</p>"
                "<p>Con il nostro corso, <strong>completamente gratuito</strong>, ti forniremo tutte le "
                "competenze tecniche e pratiche necessarie per iniziare questa avventura nel mondo del calcio.</p>"
            ),
            "requirementsTitle": "Requisiti per partecipare",
            "requirements": [
                {
                    "icon": "Calendar",
                    "text": "Età compresa tra 14 e 40 anni (14 anni compiuti – 40 anni non compiuti)",
                },
                {
                    "icon": "Globe",
                    "text": "Essere cittadino dell'Unione Europea o avere regolare permesso di soggiorno",
                },
                {
                    "icon": "HeartPulse",
                    "text": "Certificato medico di idoneità sportiva agonistica",
                },
                {
                    "icon": "Sparkles",
                    "text": "Nessuna esperienza richiesta: ti insegneremo tutto noi",
                },
                {
                    "icon": "BookOpen",
                    "text": "Impegno di due lezioni settimanali per circa due mesi",
                },
                {
                    "icon": "ClipboardCheck",
                    "text": "Superamento di una prova teorica sul regolamento e di una prova atletica",
                },
                {
                    "icon": "Flame",
                    "text": "Voglia di mettersi in gioco e passione per il calcio",
                },
                {
                    "icon": "CalendarDays",
                    "text": "Disponibilità nel fine settimana per dirigere le partite",
                },
            ],
            "imageAspect": "3:4",
            "imagePosition": "right",
            "badgeLabel": "100%",
            "badgeText": "Corso gratuito",
        },
        "stats": {
            "eyebrow": "Perché diventare arbitro",
            "title": "I vantaggi di indossare il fischietto",
            "background": "slate",
            "items": [
                {
                    "icon": "Trophy",
                    "value": "",
                    "label": "Rimborsi economici",
                    "desc": "Ricevi da subito un rimborso spese per ogni partita, a partire da 36€ in base alla categoria e alla distanza.",
                },
                {
                    "icon": "Star",
                    "value": "",
                    "label": "Ingresso gratuito agli stadi",
                    "desc": "Con la tessera federale FIGC puoi richiedere l'accredito per accedere gratuitamente agli stadi d'Italia.",
                },
                {
                    "icon": "Users",
                    "value": "",
                    "label": "Doppio tesseramento",
                    "desc": "Fino ai 19 anni puoi essere sia arbitro sia calciatore, senza rinunciare a nessuna delle due passioni.",
                },
                {
                    "icon": "Zap",
                    "value": "",
                    "label": "Preparazione atletica",
                    "desc": "Allenamenti gratuiti con preparatori qualificati e programma personalizzato per essere sempre al top.",
                },
                {
                    "icon": "Award",
                    "value": "",
                    "label": "Kit completo gratuito",
                    "desc": "Divisa ufficiale, fischietto, taccuino e tutto il materiale tecnico necessario per iniziare.",
                },
                {
                    "icon": "GraduationCap",
                    "value": "",
                    "label": "Crediti formativi",
                    "desc": "L'attività arbitrale è riconosciuta come credito formativo scolastico per conciliare sport e studio.",
                },
            ],
        },
        "timeline": {
            "eyebrow": "Il percorso",
            "title": "Come diventare arbitro",
            "items": [
                {
                    "step": "01",
                    "title": "Iscrizione al corso",
                    "text": "Compila il modulo in questa pagina. Verrai contattato per confermare la partecipazione al prossimo corso disponibile.",
                },
                {
                    "step": "02",
                    "title": "Frequenza del corso",
                    "text": "Il corso dura circa due mesi con due lezioni settimanali: regolamento, gestione della gara e tecniche arbitrali.",
                },
                {
                    "step": "03",
                    "title": "Esame finale",
                    "text": "Al termine del corso supererai un esame teorico sul regolamento. Con il superamento, sarai ufficialmente arbitro di calcio.",
                },
                {
                    "step": "04",
                    "title": "Prime esperienze sul campo",
                    "text": "Inizierai con le categorie giovanili, accompagnato da un tutor che ti seguirà nei primi passi con feedback e consigli.",
                },
                {
                    "step": "05",
                    "title": "Crescita e carriera",
                    "text": "Con esperienza e buoni risultati potrai essere promosso a categorie superiori. L'AIA ti supporterà con formazione continua.",
                },
            ],
        },
        "testimonials": {
            "eyebrow": "Voci dalla sezione",
            "title": "Cosa dicono i nostri arbitri",
            "useGlobal": True,
            "items": [],
        },
        "cta": {
            "anchor": "form",
            "eyebrow": "Preiscrizione",
            "title": "Iscriviti al corso",
            "description": (
                "Compila il modulo di iscrizione: verrai contattato per confermare "
                "la tua partecipazione al prossimo corso della Sezione AIA Legnano."
            ),
            "style": "navy",
            "formType": "corso-arbitri",
        },
        "faq": {
            "eyebrow": "Domande frequenti",
            "title": "Hai dubbi? Te li risolviamo subito.",
            "background": "slate",
            "items": [
                {
                    "question": "Posso essere sia calciatore che arbitro?",
                    "answer": (
                        "<p>Sì, grazie al doppio tesseramento, ragazze e ragazzi tra i 14 e i 19 anni possono essere "
                        "tesserati sia come calciatori sia come arbitri. Non potrai arbitrare partite nei gironi "
                        "in cui gioca la tua squadra.</p>"
                    ),
                },
                {
                    "question": "Quanto costa il corso per diventare arbitro?",
                    "answer": (
                        "<p>Il corso è <strong>completamente gratuito</strong>. Gli unici costi a tuo carico sono "
                        "il certificato medico di idoneità sportiva agonistica (circa 50€) e le scarpe da calcio.</p>"
                    ),
                },
                {
                    "question": "Che tipo di impegno richiede l'attività arbitrale?",
                    "answer": (
                        "<p>L'impegno principale è nel fine settimana per dirigere le partite assegnate "
                        "(generalmente una a settimana). In settimana sono previsti allenamenti facoltativi e "
                        "una riunione tecnica mensile, conciliabili con studio e lavoro.</p>"
                    ),
                },
                {
                    "question": "A quanto ammonta il rimborso per ogni partita?",
                    "answer": (
                        "<p>Il rimborso varia in base alla categoria e alla distanza dal campo. "
                        "Per le categorie giovanili e provinciali si parte mediamente dai <strong>36€</strong> a partita.</p>"
                    ),
                },
                {
                    "question": "E se non conosco bene le regole del calcio?",
                    "answer": (
                        "<p>Non preoccuparti: il corso è pensato per insegnarti tutto da zero. "
                        "Gli istruttori spiegheranno il regolamento con esempi pratici ed esercitazioni sul campo.</p>"
                    ),
                },
                {
                    "question": "Sono previste quote associative annuali?",
                    "answer": (
                        "<p>Sì, è prevista una quota associativa annuale che comprende assicurazione e tessera federale, "
                        "con cui puoi richiedere l'accesso gratuito agli stadi per le partite organizzate dalla FIGC.</p>"
                    ),
                },
            ],
        },
    }


def _diventa_arbitro_blocks():
    """Blocchi pagina Diventa Arbitro (testi AIA FIGC + immagini seed)."""
    cfg = _diventa_arbitro_block_configs()
    return [
        _block(
            "hero",
            {
                **cfg["hero"],
                "backgroundImage": "https://images.unsplash.com/photo-1574629810360-7efbbe195018?q=85&w=2000&auto=format&fit=crop",
            },
        ),
        _block(
            "text_image",
            {
                **cfg["text_image"],
                "imageUrl": "https://images.unsplash.com/photo-1577471488278-16eec37ffcc2?q=85&w=750&h=1000&auto=format&fit=crop",
            },
        ),
        _block("stats", cfg["stats"]),
        _block("timeline", cfg["timeline"]),
        _block("testimonials", cfg["testimonials"]),
        _block("cta", cfg["cta"]),
        _block("faq", cfg["faq"]),
    ]


def _apply_diventa_arbitro_texts(blocks: list) -> list:
    """Aggiorna solo i testi dei blocchi Diventa Arbitro, preserva id e media."""
    cfg = _diventa_arbitro_block_configs()
    media_keys = {
        "hero": (
            "backgroundImage",
            "backgroundImageSource",
            "badgeLogoUrl",
            "badgeLogoSource",
        ),
        "text_image": ("imageUrl", "imageUrlSource"),
        "cta": ("backgroundImage", "backgroundImageSource"),
    }
    out = []
    for block in blocks:
        btype = block.get("type")
        if btype not in cfg:
            out.append(block)
            continue
        old = block.get("config") or {}
        merged = {**old, **cfg[btype]}
        for key in media_keys.get(btype, ()):
            if old.get(key):
                merged[key] = old[key]
        out.append({**block, "config": merged})
    return out


async def ensure_diventa_arbitro_content_aia():
    """Diventa Arbitro: testi allineati al portale nazionale AIA FIGC."""
    db = get_db()
    page = await db.pages.find_one({"slug": "diventa-arbitro"}, {"_id": 0})
    if not page:
        return
    blocks = _apply_diventa_arbitro_texts(page.get("blocks") or [])
    await db.pages.update_one(
        {"slug": "diventa-arbitro"},
        {
            "$set": {
                "blocks": blocks,
                "summary": (
                    "Vivi il calcio da protagonista! Corso gratuito per arbitri "
                    "della Sezione AIA Legnano."
                ),
                "metaDescription": (
                    "Corso arbitri gratuito AIA Legnano: iscrizioni aperte, formazione completa, "
                    "kit e rimborsi. Diventa arbitro di calcio con la nostra sezione."
                ),
            }
        },
    )
    logger.info("Diventa Arbitro: testi aggiornati (AIA FIGC)")


def build_system_pages():
    """Initial block-based content for Home and Diventa Arbitro."""
    home_blocks = [
        _block(
            "hero",
            {
                "eyebrow": "Sezione AIA Legnano · Dal 1927",
                "title": "Ogni decisione nasce da preparazione e coraggio.",
                "subtitle": "Sezione Associazione Italiana Arbitri di Legnano. Punto di riferimento per arbitri, osservatori e aspiranti del territorio dell'Alto Milanese.",
                "backgroundImage": "https://images.unsplash.com/photo-1551958219-acbc608c6377?q=85&w=2560&auto=format&fit=crop",
                "overlay": "navy",
                "height": "tall",
                "badgeLogoUrl": "/brand/logo-aia-legnano.png",
                "primaryCta": {"label": "Diventa Arbitro", "href": "/diventa-arbitro"},
                "secondaryCta": {"label": "", "href": ""},
                "showStats": True,
            },
        ),
        _block(
            "news_slider",
            {
                "eyebrow": "Aggiornamenti",
                "title": "Vita sezionale e successi",
                "limit": 3,
                "category": "",
                "ctaLabel": "Tutte le news",
                "ctaHref": "/news",
            },
        ),
        _block(
            "events_list",
            {
                "eyebrow": "Calendario sezionale",
                "title": "Prossimi eventi",
                "limit": 3,
                "upcomingOnly": True,
                "ctaLabel": "Tutti gli eventi",
                "ctaHref": "/eventi",
                "showInstagramWidget": True,
                "showCalendar": False,
                "showPresidentCard": False,
                "instagramTitle": "AIA Legnano",
                "instagramSubtitle": "Foto, aggiornamenti e vita della sezione su Instagram.",
            },
        ),
        _block(
            "cta",
            {
                "eyebrow": "Corso Arbitri · Iscrizioni aperte",
                "title": "Vivi il calcio da protagonista.",
                "description": "Il percorso formativo gratuito della Sezione AIA Legnano. Regolamento, video, preparazione atletica e testimonianze di associati esperti.",
                "backgroundImage": "/images/home-corso-arbitri.png",
                "backgroundImageSource": "/images/home-corso-arbitri.png",
                "primaryCta": {
                    "label": "Inizia il tuo percorso",
                    "href": "/diventa-arbitro",
                },
                "style": "navy",
            },
        ),
    ]
    diventa_blocks = _diventa_arbitro_blocks()
    return [
        {
            "id": "page-home",
            "slug": "home",
            "title": "Home",
            "template": "system",
            "status": "published",
            "eyebrow": "Sezione AIA Legnano",
            "heading": "AIA Legnano",
            "summary": "Sito ufficiale della Sezione Associazione Italiana Arbitri di Legnano.",
            "image": "",
            "bodyHtml": "",
            "blocks": home_blocks,
            "primaryCtaLabel": "",
            "primaryCtaHref": "",
            "secondaryCtaLabel": "",
            "secondaryCtaHref": "",
            "metaTitle": "AIA Legnano · Sezione Associazione Italiana Arbitri",
            "metaDescription": "Sito ufficiale della Sezione AIA di Legnano. News, designazioni, corso arbitri, attività della sezione dell'Alto Milanese.",
            "showInMenu": True,
            "menuLabel": "Home",
            "menuOrder": 1,
            "updatedAt": _now(),
        },
        {
            "id": "page-diventa-arbitro",
            "slug": "diventa-arbitro",
            "title": "Diventa Arbitro",
            "template": "system",
            "status": "published",
            "eyebrow": "Corso arbitri",
            "heading": "Diventa Arbitro di Calcio",
            "summary": "Vivi il calcio da protagonista! Corso gratuito per arbitri della Sezione AIA Legnano.",
            "image": "",
            "bodyHtml": "",
            "blocks": diventa_blocks,
            "primaryCtaLabel": "",
            "primaryCtaHref": "",
            "secondaryCtaLabel": "",
            "secondaryCtaHref": "",
            "metaTitle": "Diventa Arbitro · AIA Legnano",
            "metaDescription": "Corso arbitri gratuito AIA Legnano: iscrizioni aperte, formazione completa, kit e rimborsi.",
            "showInMenu": False,
            "menuLabel": "",
            "menuOrder": 0,
            "updatedAt": _now(),
        },
    ]


async def seed_articles():
    db = get_db()
    if await db.articles.count_documents({}) > 0:
        return
    data = _read("news.json")
    for n in data:
        slug = n.get("slug")
        if slug in SKIP_NEWS_SLUGS:
            continue
        title = n.get("titolo") or n.get("title") or ""
        category = n.get("categoria") or "Vita sezionale"
        excerpt = (n.get("anteprima") or "").strip()
        published = n.get("data") or _now()[:10]
        body = ARTICLE_BODIES.get(slug)
        if not body:
            body_text = (n.get("contenuto") or "").strip()
            if body_text:
                paras = [x.strip() for x in body_text.split("\n") if x.strip()]
                body = "\n".join(f"<p>{x}</p>" for x in paras)
            else:
                body = f"<p>{excerpt}</p>"
        cover = NEWS_IMAGES.get(slug) or n.get("immagine") or ""
        art = Article(
            slug=slug,
            title=title,
            category=category,
            excerpt=excerpt,
            bodyHtml=sanitize_html(body),
            coverUrl=cover,
            publishedAt=f"{published}T08:00:00+00:00",
        )
        await db.articles.insert_one(art.model_dump().copy())


async def seed_events():
    db = get_db()
    if await db.events.count_documents({}) > 0:
        return
    data = _read("events.json")
    for e in data:
        ev = Event(
            date=e["data"],
            titolo=e["titolo"],
            descrizione=e.get("descrizione", ""),
            luogo=e.get("luogo", ""),
            tipo=e.get("tipo", "Riunione"),
        )
        await db.events.insert_one(ev.model_dump().copy())


# Real-ish referee portraits (Unsplash) for officials
OFFICIAL_PHOTOS = [
    "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?auto=format&fit=crop&w=600&q=80",
    "https://images.unsplash.com/photo-1494790108377-be9c29b29330?auto=format&fit=crop&w=600&q=80",
    "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?auto=format&fit=crop&w=600&q=80",
    "https://images.unsplash.com/photo-1438761681033-6461ffad8d80?auto=format&fit=crop&w=600&q=80",
    "https://images.unsplash.com/photo-1519085360753-af0119f7cbe7?auto=format&fit=crop&w=600&q=80",
    "https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?auto=format&fit=crop&w=600&q=80",
    "https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?auto=format&fit=crop&w=600&q=80",
    "https://images.unsplash.com/photo-1487412720507-e7ab37603c6f?auto=format&fit=crop&w=600&q=80",
]


async def seed_officials():
    """Inserisce organigramma demo solo al primo seed (mai dopo cancellazioni admin)."""
    if await _seed_flag("officials"):
        return
    db = get_db()
    data = _read("organigramma.json")
    for i, o in enumerate(data):
        slug = slugify(f"{o['nome']}-{o['cognome']}")
        if slug in DEMO_MEMBER_SLUGS:
            continue
        if await db.members.find_one({"slug": slug}, {"_id": 0, "id": 1}):
            continue
        ruolo = o["ruolo"]
        member = Member(
            slug=slug,
            firstName=o["nome"],
            lastName=o["cognome"],
            memberRole="consiglio_direttivo",
            boardTitle=ruolo,
            isPresident=ruolo.lower() == "presidente",
            photoUrl=o.get("foto") or OFFICIAL_PHOTOS[i % len(OFFICIAL_PHOTOS)],
        )
        await db.members.insert_one(member.model_dump().copy())
    await _set_seed_flag("officials")


async def seed_members():
    if await _seed_flag("associati"):
        return
    db = get_db()
    data = _read("associati.json")
    from .member_roles import member_role_from_seed_category

    for a in data:
        slug = slugify(f"{a['nome']}-{a['cognome']}")
        if slug in DEMO_MEMBER_SLUGS:
            continue
        if await db.members.find_one({"slug": slug}, {"_id": 0, "id": 1}):
            continue
        cat = a.get("categoria", "")
        mrole = member_role_from_seed_category(cat)
        observer_type = ""
        if mrole == "osservatore":
            observer_type = "ot" if "organo tecnico" in cat.lower() else "oa"
        member = Member(
            slug=slug,
            firstName=a["nome"],
            lastName=a["cognome"],
            memberRole=mrole,
            observerType=observer_type,
            category=cat,
            yearStart=a.get("anno_inizio"),
        )
        await db.members.insert_one(member.model_dump().copy())
    await _set_seed_flag("associati")


async def seed_designations():
    db = get_db()
    if await db.designations.count_documents({}) > 0:
        return
    data = _read("designazioni.json")
    # Build name → memberId map
    members = await db.members.find({}, {"_id": 0}).to_list(500)
    name_to_id = {f"{m['firstName']} {m['lastName']}": m["id"] for m in members}
    for d in data:
        nominativo = d.get("nominativo", "")
        member_id = name_to_id.get(nominativo)
        des = Designation(
            matchDate=f"{d['data']}T15:00:00+00:00",
            category="",
            matchLabel=d["gara"],
            role=d["ruolo"],
            memberName=nominativo,
            memberId=member_id,
        )
        await db.designations.insert_one(des.model_dump().copy())


async def seed_testimonials():
    db = get_db()
    if await _seed_flag("testimonials"):
        return
    if await db.testimonials.count_documents({}) > 0:
        await _set_seed_flag("testimonials")
        return
    items = [
        {
            "name": "Francesca Conti",
            "role": "Arbitra promossa al ruolo nazionale",
            "quote": "Il corso arbitri a Legnano è stata la scelta migliore della mia vita sportiva. Ho trovato persone vere, una formazione seria e un percorso che mi ha portato fino al ruolo nazionale.",
            "photoUrl": "https://images.unsplash.com/photo-1494790108377-be9c29b29330?auto=format&fit=crop&w=400&q=80",
        },
        {
            "name": "Matteo Colombo",
            "role": "Arbitro Eccellenza · Premio Arbitro dell'Anno",
            "quote": "Quando ho iniziato non sapevo cosa aspettarmi. Oggi arbitro in Eccellenza e ho ricevuto il premio sezionale. Tutto è iniziato qui, con questo corso.",
            "photoUrl": "https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?auto=format&fit=crop&w=400&q=80",
        },
        {
            "name": "Elena Sala",
            "role": "Referente Corso Arbitri",
            "quote": "Dirigere il corso a Legnano significa accompagnare ragazze e ragazzi in un percorso che cambia il modo di vedere il calcio. È un onore vedere quanti giovani crescono ogni anno.",
            "photoUrl": "https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?auto=format&fit=crop&w=400&q=80",
        },
    ]
    for i, t in enumerate(items):
        from .models import Testimonial as TM

        await db.testimonials.insert_one(TM(**t, sortOrder=i).model_dump().copy())
    await _set_seed_flag("testimonials")


async def seed_documents():
    """Documenti demo — saltato se la collezione ha già contenuti."""
    db = get_db()
    if await db.documents.count_documents({}) > 0:
        return
    items = [
        {
            "title": "Regolamento del Gioco del Calcio 2025/26",
            "description": "Edizione ufficiale FIGC con aggiornamenti annuali.",
            "fileUrl": "https://www.figc.it/",
            "fileSize": "2.4 MB",
            "category": "regolamento",
            "sortOrder": 1,
        },
        {
            "title": "Modulo iscrizione corso arbitri",
            "description": "PDF da compilare per la pre-iscrizione cartacea.",
            "fileUrl": "#",
            "fileSize": "180 KB",
            "category": "modulistica",
            "sortOrder": 2,
        },
        {
            "title": "Linee guida atletica arbitrale",
            "description": "Programma di preparazione atletica per associati.",
            "fileUrl": "#",
            "fileSize": "1.1 MB",
            "category": "tecnica",
            "sortOrder": 3,
        },
    ]
    for it in items:
        from .models import Document as Doc

        await db.documents.insert_one(Doc(**it).model_dump().copy())


async def ensure_aia_download_documents():
    """Importa documenti ufficiali da aia-figc.it/download (una volta, poi da admin)."""
    if await _seed_flag("aia_download_documents"):
        return 0
    from .scrapers.aia_downloads import import_aia_downloads

    db = get_db()
    result = await import_aia_downloads(db, download_files=True, replace_existing=True)
    await _set_seed_flag("aia_download_documents")
    return result.get("imported", 0)


async def ensure_document_section_categories():
    """Allinea category/section e catalogo sezioni in site_settings."""
    from .document_sections import (
        ensure_document_sections_seed,
        migrate_legacy_document_categories,
    )

    db = get_db()
    updated = await migrate_legacy_document_categories(db)
    await ensure_document_sections_seed(db)
    if updated:
        logger.info("Categorie documenti allineate: %s record", updated)
    return updated


async def ensure_aia_legnano_download_documents():
    """Importa documenti da aia-legnano.it/download (una volta, poi da admin)."""
    if await _seed_flag("aia_legnano_download_documents"):
        return 0
    from .scrapers.aia_legnano_downloads import import_legnano_downloads

    db = get_db()
    result = await import_legnano_downloads(
        db, download_files=True, replace_existing=True
    )
    await _set_seed_flag("aia_legnano_download_documents")
    return result.get("imported", 0)


async def ensure_event_invites_migrated():
    """Copia relatedMemberIds → invitedMemberIds sugli eventi legacy."""
    db = get_db()
    cursor = db.events.find(
        {"relatedMemberIds": {"$exists": True, "$ne": []}},
        {"_id": 0, "id": 1, "relatedMemberIds": 1, "invitedMemberIds": 1},
    )
    async for ev in cursor:
        if ev.get("invitedMemberIds"):
            continue
        await db.events.update_one(
            {"id": ev["id"]},
            {"$set": {"invitedMemberIds": ev.get("relatedMemberIds") or []}},
        )


async def ensure_gallery_member_tags() -> int:
    """Tag associati sulle immagini da articoli che citano nome e cognome."""
    from .gallery_member_tags import ensure_gallery_member_tags as _ensure

    db = get_db()
    return await _ensure(db)


async def ensure_gallery_backfill_from_articles() -> int:
    """Import iniziale galleria da articoli; metadati ad ogni avvio, rigenerazione solo una volta."""
    from .gallery import backfill_gallery_from_articles, ensure_gallery_metadata

    db = get_db()
    await ensure_gallery_metadata(db)
    if await _seed_flag("gallery_curated_backfill"):
        return 0
    if await db.gallery_images.count_documents({}) > 0:
        await _set_seed_flag("gallery_curated_backfill")
        return 0
    n = await backfill_gallery_from_articles(db)
    await _set_seed_flag("gallery_curated_backfill")
    return n


async def ensure_instagram_gallery_deduped() -> int:
    from .instagram_gallery_dedupe import dedupe_instagram_gallery

    db = get_db()
    n = await dedupe_instagram_gallery(db)
    if n:
        logger.info("Galleria Instagram: rimossi %s duplicati", n)
    return n


async def ensure_instagram_gallery_sync() -> dict | None:
    """Sincronizza galleria da Instagram se INSTAGRAM_SESSION_ID è configurato."""
    import os

    session_id = os.getenv("INSTAGRAM_SESSION_ID", "").strip()
    if not session_id:
        return None
    from .instagram_gallery import sync_instagram_gallery

    db = get_db()
    settings = (
        await db.settings.find_one({"_id": "site"}, {"_id": 0, "instagramUrl": 1}) or {}
    )
    result = await sync_instagram_gallery(
        db,
        username=settings.get("instagramUrl")
        or "https://www.instagram.com/aia_legnano/",
        session_id=session_id,
        since_year=2021,
        limit=0,
    )
    if result.get("added"):
        logger.info("Instagram galleria: importate %s immagini", result["added"])
    return result


async def purge_demo_gallery_images() -> int:
    """Rimuove immagini demo (picsum) dalla galleria admin."""
    db = get_db()
    res = await db.gallery_images.delete_many(
        {"url": {"$regex": r"picsum\.photos", "$options": "i"}}
    )
    if res.deleted_count:
        logger.info("Rimosse %s immagini demo dalla galleria", res.deleted_count)
    return res.deleted_count


async def ensure_osservatori_page(db=None):
    """Crea/aggiorna pagina Osservatori e allinea titoli Arbitri / menu."""
    from .blocks_sanitize import sanitize_blocks
    from .system_page_blocks import default_blocks_for_slug

    if db is None:
        db = get_db()

    blocks = sanitize_blocks(default_blocks_for_slug("osservatori"))
    desired = {
        "title": "Osservatori",
        "template": "system",
        "status": "published",
        "eyebrow": "Sezione Legnano",
        "heading": "Osservatori",
        "summary": "Osservatori arbitrali (OA) e Organo Tecnico (OT) della sezione.",
        "showInMenu": True,
        "menuLabel": "Osservatori",
        "menuOrder": 5,
        "menuHighlight": False,
        "metaTitle": "Osservatori · AIA Legnano",
        "metaDescription": "Osservatori arbitrali (OA) e Organo Tecnico (OT) della sezione.",
    }
    existing = await db.pages.find_one({"slug": "osservatori"}, {"_id": 0})
    if not existing:
        doc = Page(slug="osservatori", blocks=blocks, **desired).model_dump().copy()
        await db.pages.insert_one(doc)
        logger.info("Pagina sistema creata: osservatori")
    else:
        patch = {k: v for k, v in desired.items()}
        if not existing.get("blocks"):
            patch["blocks"] = blocks
        await db.pages.update_one({"slug": "osservatori"}, {"$set": patch})

    # Allinea testo pagina Arbitri (non sovrascrivere se già personalizzato con altro senso)
    arbitri = await db.pages.find_one({"slug": "arbitri"}, {"_id": 0, "summary": 1})
    if arbitri:
        summary = (arbitri.get("summary") or "").lower()
        if "chi siamo" in summary or not (arbitri.get("summary") or "").strip():
            await db.pages.update_one(
                {"slug": "arbitri"},
                {
                    "$set": {
                        "summary": "Arbitri effettivi, assistenti arbitrali e arbitri benemeriti della sezione.",
                    }
                },
            )

    # Rimuovi boardTitle generico AB (non è incarico di organigramma)
    cleared = await db.members.update_many(
        {
            "$or": [
                {"role": {"$in": ["AB", "ab"]}},
                {"category": {"$regex": "benemerito", "$options": "i"}},
            ],
            "boardTitle": {"$regex": r"^\s*arbitro\s+benemerito\s*$", "$options": "i"},
        },
        {"$set": {"boardTitle": ""}},
    )
    if cleared.modified_count:
        logger.info("Puliti boardTitle Benemerito generici: %s", cleared.modified_count)


async def run_all():
    await seed_admin()
    await seed_settings()
    await purge_demo_members()
    await ensure_legacy_seed_flags()
    await seed_pages()
    await ensure_all_system_pages()
    await ensure_osservatori_page()
    await ensure_chi_siamo_content()
    await ensure_compact_header_pages()
    await ensure_chi_siamo_story_block_layout()
    await ensure_article_categories_seed()
    await ensure_event_types_seed()
    await ensure_raduni_article_categories()
    await ensure_home_events_limit()
    await ensure_eventi_list_layout()
    await ensure_home_corso_arbitri_cta_image()
    await ensure_diventa_arbitro_content_aia()
    await ensure_diventa_arbitro_testimonials()
    await ensure_diventa_arbitro_text_image_aspect()
    await ensure_section_logo_in_blocks()
    await ensure_event_invites_migrated()
    await purge_demo_gallery_images()
    await seed_articles()
    n = await ensure_gallery_backfill_from_articles()
    if n:
        logger.info("Galleria: %s immagini approvate (backfill articoli)", n)
    n_tags = await ensure_gallery_member_tags()
    if n_tags:
        logger.info("Galleria: tag associati su %s immagini", n_tags)
    await ensure_instagram_gallery_deduped()
    await ensure_instagram_gallery_sync()
    await seed_events()
    await seed_officials()
    await seed_members()
    await seed_designations()
    await seed_testimonials()
    await seed_documents()
    n_docs = await ensure_aia_download_documents()
    if n_docs:
        logger.info("Documenti AIA FIGC importati: %s", n_docs)
    n_legnano = await ensure_aia_legnano_download_documents()
    if n_legnano:
        logger.info("Documenti AIA Legnano importati: %s", n_legnano)
    await ensure_document_section_categories()
    from .utility_migration import ensure_utility_seed

    await ensure_utility_seed(db=None)
