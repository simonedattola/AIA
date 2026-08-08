"""Ruoli sezionali unificati (gestiti dalla pagina Associati in admin)."""
from __future__ import annotations

import re

MEMBER_ROLES = ("arbitro", "assistente", "consiglio_direttivo", "osservatore")
ARBITRI_ROLES = frozenset({"arbitro", "assistente"})
CHI_SIAMO_ROLES = frozenset({"consiglio_direttivo", "osservatore"})
OBSERVER_TYPES = ("oa", "ot")


def _strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text or "").strip()


def infer_member_role(doc: dict) -> str:
    explicit = (doc.get("memberRole") or "").strip().lower()
    if explicit in MEMBER_ROLES:
        return explicit
    # legacy valori con maiuscole / etichette UI
    legacy_map = {
        "arbitro": "arbitro",
        "assistente": "assistente",
        "consiglio direttivo": "consiglio_direttivo",
        "consiglio_direttivo": "consiglio_direttivo",
        "osservatore": "osservatore",
        "oa": "osservatore",
        "ot": "osservatore",
    }
    if explicit in legacy_map:
        return legacy_map[explicit]

    kind = (doc.get("kind") or "").strip().lower()
    role = (doc.get("role") or "").strip().lower()

    if kind in ("oa", "ot") or kind == "osservatore" or "osservatore" in role:
        return "osservatore"
    if "assistente" in role or kind == "tutor":
        return "assistente"
    if kind == "associato" and "assistente" in role:
        return "assistente"
    return "arbitro"


def infer_observer_type(doc: dict) -> str:
    ot = (doc.get("observerType") or "").strip().lower()
    if ot in OBSERVER_TYPES:
        return ot
    kind = (doc.get("kind") or "").strip().lower()
    if kind == "ot":
        return "ot"
    cat = (doc.get("category") or "").lower()
    if "organo tecnico" in cat or cat.strip() in ("ot", "ots"):
        return "ot"
    return "oa"


def normalize_member(doc: dict) -> dict:
    """Allinea documento DB al modello ruoli unificato (in-place)."""
    doc["memberRole"] = infer_member_role(doc)
    if doc["memberRole"] == "osservatore":
        doc["observerType"] = infer_observer_type(doc)
    if not doc.get("boardTitle") and doc["memberRole"] == "consiglio_direttivo":
        legacy = (doc.get("role") or "").strip()
        if legacy and legacy.lower() not in ("arbitro", "assistente", "oa", "ot", "tutor"):
            doc["boardTitle"] = legacy
    bt = (doc.get("boardTitle") or "").strip().lower()
    if bt:
        # Presidente di Sezione only (not Vice, not Organo di Revisione)
        if "revisione" in bt or "revisori" in bt or "vice" in bt:
            doc["isPresident"] = False
        elif "presidente di sezione" in bt or bt in ("presidente", "presidente di sezione"):
            doc["isPresident"] = True
        elif "presidente" in bt and "sezione" in bt:
            doc["isPresident"] = True
    bio = (doc.get("bio") or "").strip()
    if not bio and doc.get("bioHtml"):
        doc["bio"] = _strip_html(doc.get("bioHtml") or "")
    return doc


def public_member(doc: dict) -> dict:
    """Campi esposti sul sito pubblico (senza note private né codice meccanografico)."""
    normalize_member(doc)
    out = {k: v for k, v in doc.items() if k not in ("notes", "meccanografico", "passwordHash")}
    return out


def has_designations(member_role: str | None) -> bool:
    return (member_role or "") in ARBITRI_ROLES


def is_observer_designation_role(role: str | None) -> bool:
    return "osservatore" in (role or "").lower()


def arbitri_query() -> dict:
    return {"memberRole": {"$in": list(ARBITRI_ROLES)}}


def chi_siamo_query() -> dict:
    """Organigramma / Chi siamo: CD, osservatori, oppure incarico sezionale (boardTitle).

    Così un arbitro può restare ``memberRole=arbitro`` (lista Associati + designazioni)
    e comparire anche in organigramma se ha ``boardTitle`` (es. Collaboratore Area Informatica).
    """
    return {
        "$or": [
            {"memberRole": {"$in": list(CHI_SIAMO_ROLES)}},
            {"boardTitle": {"$exists": True, "$nin": ["", None]}},
        ]
    }


def legacy_arbitri_query() -> dict:
    """Compatibilità dati senza memberRole."""
    return {
        "$or": [
            {"memberRole": {"$in": list(ARBITRI_ROLES)}},
            {
                "memberRole": {"$exists": False},
                "kind": {"$in": ["associato", "tutor"]},
            },
        ]
    }


def legacy_chi_siamo_query() -> dict:
    return {
        "$or": [
            {"memberRole": {"$in": list(CHI_SIAMO_ROLES)}},
            {"boardTitle": {"$exists": True, "$nin": ["", None]}},
            {
                "memberRole": {"$exists": False},
                "kind": {"$in": ["oa", "ot", "osservatore"]},
            },
        ]
    }


def member_role_label(member_role: str | None, observer_type: str | None = None) -> str:
    r = (member_role or "").lower()
    if r == "arbitro":
        return "Arbitro"
    if r == "assistente":
        return "Assistente"
    if r == "consiglio_direttivo":
        return "Consiglio Direttivo"
    if r == "osservatore":
        ot = (observer_type or "oa").lower()
        return "OA" if ot == "oa" else "OT"
    return ""


def observer_subtitle(observer_type: str | None) -> str:
    return "Organo Tecnico" if (observer_type or "").lower() == "ot" else "Osservatore Arbitrale"


def member_role_from_seed_category(category: str) -> str:
    c = (category or "").lower()
    if "organo tecnico" in c or "osservatore" in c:
        return "osservatore"
    if "assistente" in c or "tutor" in c:
        return "assistente"
    return "arbitro"
