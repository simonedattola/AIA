"""Ruoli sezionali unificati (gestiti dalla pagina Associati in admin)."""

from __future__ import annotations

import re

MEMBER_ROLES = ("arbitro", "assistente", "consiglio_direttivo", "osservatore")
ARBITRI_ROLES = frozenset({"arbitro", "assistente"})
CHI_SIAMO_ROLES = frozenset({"consiglio_direttivo"})
OBSERVER_TYPES = ("oa", "ot")
ORGANIGRAMMA_KINDS = ("cds", "collaboratore", "ors")
AIA_CODES = ("AE", "AA", "AB", "AFR", "OA", "OT")
ROLE_GROUP_AIA = AIA_CODES
ROLE_GROUP_ORG = ORGANIGRAMMA_KINDS
VALID_ROLE_GROUPS = ROLE_GROUP_AIA + ROLE_GROUP_ORG
AIA_CODE_TO_MEMBER_ROLE = {
    "AE": "arbitro",
    "AA": "assistente",
    "AB": "arbitro",
    "AFR": "arbitro",
    "OA": "osservatore",
    "OT": "osservatore",
}
# Categoria massima campionato: solo Arbitro Effettivo e Assistente Arbitrale
CATEGORY_ELIGIBLE_CODES = frozenset({"AE", "AA"})

# boardTitle generico AB: non è incarico di organigramma
_BENEMERITO_TITLE = re.compile(r"^\s*arbitro\s+benemerito\s*$", re.I)
_VICE_PRESIDENTE = re.compile(r"vice\s*-?\s*presidente|vicepresidente", re.I)
_PRESIDENTE_WORD = re.compile(r"\bpresidente\b", re.I)


def _strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text or "").strip()


def aia_code_of(doc: dict | None) -> str:
    if not doc:
        return ""
    code = (doc.get("role") or "").strip().upper()
    return code if code in AIA_CODE_TO_MEMBER_ROLE else ""


def can_have_max_category(doc: dict | None) -> bool:
    """
    Categoria massima: AE/AA, oppure associati con memberRole arbitro/assistente
    creati dalla sync senza codice AIA (role testuale «Arbitro»/«Assistente»).
    Esclusi AB, AFR, OA, OT e altri codici non eleggibili.
    """
    if not doc:
        return False
    code = aia_code_of(doc)
    if code in CATEGORY_ELIGIBLE_CODES:
        return True
    if code:
        # Altro codice AIA esplicito (AB, AFR, OA, OT, …)
        return False
    mrole = (doc.get("memberRole") or "").strip().lower()
    if mrole in ARBITRI_ROLES:
        return True
    if mrole:
        return False
    role_label = (doc.get("role") or "").strip().lower()
    return role_label in {"arbitro", "assistente"}


def infer_organigramma_kind(doc: dict) -> str:
    explicit = (doc.get("organigrammaKind") or "").strip().lower()
    if explicit in ORGANIGRAMMA_KINDS:
        return explicit
    if explicit in ("", "none", "nessuno"):
        # continua con inferenza da titoli legacy
        pass
    else:
        return ""

    bt = (doc.get("boardTitle") or "").strip()
    if not bt or _BENEMERITO_TITLE.match(bt):
        # Solo consiglio_direttivo legacy senza titolo → CDS
        if (doc.get("memberRole") or "").strip().lower() == "consiglio_direttivo":
            return "cds"
        return ""

    low = bt.lower()
    if "revisione" in low or "revisori" in low:
        return "ors"
    if (
        re.match(r"^\s*collaboratore\b", low)
        or "collaboratore —" in low
        or "collaboratore -" in low
    ):
        return "collaboratore"
    if (
        "consigliere" in low
        or _VICE_PRESIDENTE.search(low)
        or "presidente di sezione" in low
        or re.match(r"^\s*presidente\b", low)
        or "segretario" in low
        or "cassiere" in low
        or (doc.get("memberRole") or "").strip().lower() == "consiglio_direttivo"
    ):
        return "cds"
    # Incarico libero (es. "Area Informatica") → collaboratore se presente
    if has_organigramma_board_title(doc):
        return "collaboratore"
    return ""


def is_section_president_title(board_title: str, organigramma_kind: str = "") -> bool:
    """Presidente di Sezione: parola Presidente in incarico CDS, non Vice/Revisione."""
    kind = (organigramma_kind or "").strip().lower()
    bt = (board_title or "").strip()
    if kind and kind != "cds":
        return False
    if not bt:
        return False
    low = bt.lower()
    if "revisione" in low or "revisori" in low:
        return False
    if _VICE_PRESIDENTE.search(bt):
        return False
    if not _PRESIDENTE_WORD.search(bt):
        return False
    # Se kind non è noto, richiedi indizi CDS (non solo "Presidente" generico in ORS già escluso)
    if not kind:
        if "collaboratore" in low:
            return False
    return True


def infer_member_role(doc: dict) -> str:
    code = aia_code_of(doc)
    if code:
        return AIA_CODE_TO_MEMBER_ROLE[code]

    kind = (doc.get("kind") or "").strip().lower()
    role = (doc.get("role") or "").strip().lower()
    cat = (doc.get("category") or "").lower()

    if kind in ("oa", "ot") or kind == "osservatore" or "osservatore" in role:
        return "osservatore"
    if re.search(r"osservatore|organo\s+tecnico", cat):
        return "osservatore"

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

    # Codice AIA AA = Assistente Arbitrale
    code_raw = (doc.get("role") or "").strip().upper()
    if code_raw == "AA" or "assistente" in role or kind == "tutor":
        return "assistente"
    if kind == "associato" and "assistente" in role:
        return "assistente"

    org = infer_organigramma_kind(doc)
    if org == "cds" and not code:
        return "consiglio_direttivo"
    return "arbitro"


def infer_observer_type(doc: dict) -> str:
    code = aia_code_of(doc)
    if code == "OT":
        return "ot"
    if code == "OA":
        return "oa"
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


def is_arbitro_benemerito(doc: dict | None) -> bool:
    """AIA code AB = Arbitro Benemerito (lista Arbitri + filtro dedicato)."""
    if not doc:
        return False
    if aia_code_of(doc) == "AB":
        return True
    cat = (doc.get("category") or "").strip().lower()
    return "benemerito" in cat


def has_organigramma_board_title(doc: dict | None) -> bool:
    """Incarico sezionale reale (CD / collaboratore / revisione), non solo Benemerito."""
    if not doc:
        return False
    kind = (doc.get("organigrammaKind") or "").strip().lower()
    if kind in ORGANIGRAMMA_KINDS:
        return True
    bt = (doc.get("boardTitle") or "").strip()
    if not bt or _BENEMERITO_TITLE.match(bt):
        return False
    return True


def normalize_member(doc: dict) -> dict:
    """Allinea documento DB al modello ruoli unificato (in-place)."""
    code = aia_code_of(doc)
    if code:
        doc["role"] = code
    doc["organigrammaKind"] = infer_organigramma_kind(doc)
    doc["memberRole"] = infer_member_role(doc)
    if doc["memberRole"] == "osservatore":
        doc["observerType"] = infer_observer_type(doc)
    elif code in ("OA", "OT"):
        doc["observerType"] = infer_observer_type(doc)
    else:
        # non osservatore: non forzare observerType se assente
        if doc.get("observerType") and doc["memberRole"] != "osservatore":
            doc["observerType"] = ""

    if not doc.get("boardTitle") and doc["memberRole"] == "consiglio_direttivo":
        legacy = (doc.get("role") or "").strip()
        if legacy and legacy.upper() not in AIA_CODE_TO_MEMBER_ROLE:
            if legacy.lower() not in ("arbitro", "assistente", "oa", "ot", "tutor"):
                doc["boardTitle"] = legacy

    doc["isPresident"] = is_section_president_title(
        doc.get("boardTitle") or "",
        doc.get("organigrammaKind") or "",
    )

    if not can_have_max_category(doc):
        # Non cancellare in lettura se è etichetta legacy usata altrove: la pulizia
        # definitiva avviene in save/migrazione. Qui non tocchiamo category.
        pass

    bio = (doc.get("bio") or "").strip()
    if not bio and doc.get("bioHtml"):
        doc["bio"] = _strip_html(doc.get("bioHtml") or "")
    return doc


def public_member(doc: dict) -> dict:
    """Campi esposti sul sito pubblico (senza note private né codice meccanografico)."""
    from .person_names import format_person_name, format_person_name_parts

    normalize_member(doc)
    first, last = format_person_name_parts(doc.get("firstName"), doc.get("lastName"))
    if first:
        doc["firstName"] = first
    if last:
        doc["lastName"] = last
    display = format_person_name(first, last)
    if display:
        doc["displayName"] = display
    out = {
        k: v
        for k, v in doc.items()
        if k not in ("notes", "meccanografico", "passwordHash", "portalPassword")
    }
    return out


def has_designations(member_role: str | None) -> bool:
    return (member_role or "") in ARBITRI_ROLES


def is_observer_designation_role(role: str | None) -> bool:
    text = role if isinstance(role, str) else ""
    return "osservatore" in text.lower()


def arbitri_query() -> dict:
    """Lista Arbitri: effettivi, assistenti, benemeriti (non osservatori)."""
    return {"memberRole": {"$in": list(ARBITRI_ROLES)}}


def chi_siamo_query() -> dict:
    """Chi siamo / organigramma: incarichi sezionali (CDS, collaboratori, ORS)."""
    return {
        "$or": [
            {"organigrammaKind": {"$in": list(ORGANIGRAMMA_KINDS)}},
            {
                "boardTitle": {
                    "$exists": True,
                    "$nin": ["", None],
                    "$not": {
                        "$regex": r"^\s*arbitro\s+benemerito\s*$",
                        "$options": "i",
                    },
                }
            },
        ]
    }


def osservatori_query() -> dict:
    """Lista pubblica Osservatori (OA/OT), inclusi dati legacy senza memberRole."""
    return {
        "$or": [
            {"memberRole": "osservatore"},
            {"role": {"$in": ["OA", "OT", "oa", "ot"]}},
            {"kind": {"$in": ["oa", "ot", "osservatore"]}},
            {
                "category": {
                    "$regex": r"osservatore|organo\s+tecnico",
                    "$options": "i",
                }
            },
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
            {"role": {"$in": ["AE", "AA", "AB", "AFR"]}},
        ]
    }


def legacy_chi_siamo_query() -> dict:
    return chi_siamo_query()


def normalize_role_groups(groups: list[str] | None) -> list[str]:
    """Filtra e deduplica codici ruolo/gruppo (AE, cds, …)."""
    out: list[str] = []
    seen: set[str] = set()
    for raw in groups or []:
        g = (raw or "").strip()
        if not g:
            continue
        if g.upper() in ROLE_GROUP_AIA:
            key = g.upper()
        elif g.lower() in ROLE_GROUP_ORG:
            key = g.lower()
        else:
            continue
        if key not in seen:
            seen.add(key)
            out.append(key)
    return out


def member_matches_role_group(doc: dict | None, group: str) -> bool:
    if not doc:
        return False
    normalize_member(doc)
    code = aia_code_of(doc)
    org = (doc.get("organigrammaKind") or "").strip().lower()
    g = (group or "").strip()
    if g.upper() in ROLE_GROUP_AIA:
        return code == g.upper()
    if g.lower() in ROLE_GROUP_ORG:
        return org == g.lower()
    return False


def member_matches_any_role_group(doc: dict | None, groups: list[str] | None) -> bool:
    normalized = normalize_role_groups(groups)
    if not normalized:
        return False
    return any(member_matches_role_group(doc, g) for g in normalized)


def role_groups_member_query(role_groups: list[str] | None) -> dict:
    """Query MongoDB: associati con profilo che appartengono ad almeno un gruppo."""
    groups = normalize_role_groups(role_groups)
    base: dict = {
        "memberRole": {"$in": list(MEMBER_ROLES)},
        "slug": {"$exists": True, "$ne": ""},
    }
    if not groups:
        return {**base, "id": {"$exists": False}}
    or_clauses: list[dict] = []
    aia_codes = [g for g in groups if g in ROLE_GROUP_AIA]
    org_kinds = [g for g in groups if g in ROLE_GROUP_ORG]
    if aia_codes:
        or_clauses.append({"role": {"$in": aia_codes}})
    if org_kinds:
        or_clauses.append({"organigrammaKind": {"$in": org_kinds}})
    if len(or_clauses) == 1:
        return {**base, **or_clauses[0]}
    return {**base, "$or": or_clauses}


def comunicazione_visibility_or_clauses(member_id: str, member: dict | None) -> list[dict]:
    """Clausole $or per comunicazioni visibili a un associato."""
    clauses: list[dict] = [{"allMembers": True}, {"memberIds": member_id}]
    if member:
        normalize_member(member)
        code = aia_code_of(member)
        org = (member.get("organigrammaKind") or "").strip().lower()
        if code:
            clauses.append({"roleGroups": code})
        if org:
            clauses.append({"roleGroups": org})
    return clauses


def member_role_label(
    member_role: str | None, observer_type: str | None = None, doc: dict | None = None
) -> str:
    if is_arbitro_benemerito(doc):
        return "Arbitro Benemerito"
    r = (member_role or "").lower()
    code = aia_code_of(doc) if doc else ""
    if r == "arbitro" or code in ("AE", "AFR", "AB"):
        if code == "AE":
            return "Arbitro Effettivo"
        if code == "AFR":
            return "Arbitro Fuori Ruolo"
        if code == "AB":
            return "Arbitro Benemerito"
        return "Arbitro"
    if r == "assistente" or code == "AA":
        return "Assistente Arbitrale"
    if r == "consiglio_direttivo":
        return "Consiglio Direttivo"
    if r == "osservatore":
        ot = (observer_type or "oa").lower()
        return "OA" if ot == "oa" else "OT"
    return ""


def observer_subtitle(observer_type: str | None) -> str:
    return (
        "Organo Tecnico"
        if (observer_type or "").lower() == "ot"
        else "Osservatore Arbitrale"
    )


def member_role_from_seed_category(category: str) -> str:
    c = (category or "").lower()
    if "organo tecnico" in c or "osservatore" in c:
        return "osservatore"
    if "assistente" in c or "tutor" in c:
        return "assistente"
    return "arbitro"


def organigramma_kind_label(kind: str | None) -> str:
    k = (kind or "").strip().lower()
    return {
        "cds": "Consiglio Direttivo Sezionale",
        "collaboratore": "Collaboratore",
        "ors": "Organo di Revisione Sezionale",
    }.get(k, "")
