"""Import anagrafica associati da file eterogenei (CSV, Excel, PDF, Word)."""

from __future__ import annotations

import re
import unicodedata
from datetime import datetime, timezone
from typing import Any, Optional

import pandas as pd
from slugify import slugify

from .db import get_db
from .models import Member, _id
from .designations_import_extract import extract_raw_tables, _cell_str
from .member_roles import normalize_member, MEMBER_ROLES

SOURCE = "file-import"

FIELD_KEYWORDS: dict[str, list[str]] = {
    "firstName": ["nome", "firstname", "first name", "nome proprio"],
    "lastName": ["cognome", "lastname", "last name", "surname"],
    "fullName": [
        "nominativo",
        "nome cognome",
        "nome e cognome",
        "anagrafica",
        "arbitro",
        "associato",
    ],
    "memberRole": ["ruolo", "role", "qualifica", "tipo", "incarico sezionale"],
    "category": [
        "categoria",
        "category",
        "campionato",
        "livello",
        "categoria sportiva",
    ],
    "meccanografico": [
        "cod mecc",
        "cod.mecc",
        "codice meccanografico",
        "meccanografico",
        "matricola",
        "codice aia",
        "mec",
    ],
    "email": ["email", "e-mail", "mail", "posta"],
    "phone": ["telefono", "phone", "cellulare", "mobile", "tel"],
    "yearStart": ["anno", "year", "anno inizio", "yearstart", "dal", "iscritto dal"],
    "boardTitle": ["incarico", "board", "carica", "consiglio", "titolo"],
    "observerType": ["tipo osservatore", "oa ot", "observer"],
    "bio": ["bio", "biografia", "profilo", "presentazione"],
    "notes": ["note", "notes", "osservazioni", "privato"],
}

IMPORT_TEMPLATE_CSV = (
    "nome;cognome;ruolo;categoria;meccanografico;email;telefono;anno\r\n"
    "Mario;Rossi;Arbitro;;12345678;mario.rossi@email.it;3331234567;2020\r\n"
    "Sara;Bianchi;Assistente;Terza Categoria;87654321;sara.bianchi@email.it;;2021\r\n"
)


def _strip_accents(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    return "".join(c for c in text if not unicodedata.combining(c))


def _norm_label(text: str) -> str:
    text = _strip_accents(_cell_str(text).lower())
    return re.sub(r"[^a-z0-9]+", " ", text).strip()


def _normalize_name_key(text: str) -> str:
    return re.sub(r"\s+", " ", _strip_accents((text or "").strip().lower()))


def _header_score(label: str, field: str) -> float:
    norm = _norm_label(label)
    if not norm:
        return 0.0
    best = 0.0
    for kw in FIELD_KEYWORDS.get(field, []):
        kn = _norm_label(kw)
        if norm == kn:
            best = max(best, 1.0)
        elif kn in norm or norm in kn:
            best = max(best, 0.85)
        elif any(tok in norm.split() for tok in kn.split() if len(tok) > 2):
            best = max(best, 0.65)
    return best


def _split_full_name(full_name: str) -> tuple[str, str]:
    parts = re.sub(r"\s+", " ", (full_name or "").strip()).split(" ")
    if len(parts) < 2:
        return parts[0] if parts else "", ""
    return " ".join(parts[:-1]), parts[-1]


def _looks_like_email(value: str) -> bool:
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", _cell_str(value)))


def _looks_like_phone(value: str) -> bool:
    digits = re.sub(r"\D", "", value or "")
    return 8 <= len(digits) <= 15


def _looks_like_mec(value: str) -> bool:
    return bool(re.fullmatch(r"[A-Za-z0-9./-]{3,12}", _cell_str(value)))


def _looks_like_year(value: str) -> bool:
    v = _cell_str(value)
    if not v or not re.fullmatch(r"\d{4}", v):
        return False
    y = int(v)
    return 1950 <= y <= datetime.now().year + 1


def _looks_like_person(value: str) -> bool:
    text = _cell_str(value)
    if not text or len(text) < 3 or len(text) > 60:
        return False
    if _looks_like_email(text) or _looks_like_phone(text) or _looks_like_mec(text):
        return False
    parts = text.split()
    return len(parts) >= 1 and all(p[:1].isalpha() for p in parts[:4])


def _looks_like_role(value: str) -> bool:
    key = _normalize_name_key(value)
    return any(
        tok in key
        for tok in (
            "arbitro",
            "assistente",
            "consiglio",
            "osservatore",
            "presidente",
            "segretario",
            "oa",
            "ot",
            "tutor",
        )
    )


def _content_score(values: list[str], field: str) -> float:
    sample = [v for v in values if v][:25]
    if not sample:
        return 0.0
    if field == "email":
        hits = sum(1 for v in sample if _looks_like_email(v))
        return hits / len(sample)
    if field == "phone":
        hits = sum(1 for v in sample if _looks_like_phone(v))
        return hits / len(sample)
    if field == "meccanografico":
        hits = sum(1 for v in sample if _looks_like_mec(v))
        return hits / len(sample)
    if field == "yearStart":
        hits = sum(1 for v in sample if _looks_like_year(v))
        return hits / len(sample)
    if field in ("firstName", "lastName", "fullName"):
        hits = sum(1 for v in sample if _looks_like_person(v))
        return hits / len(sample)
    if field == "memberRole":
        hits = sum(1 for v in sample if _looks_like_role(v))
        return hits / len(sample)
    if field == "category":
        hits = sum(
            1
            for v in sample
            if v and not _looks_like_role(v) and not _looks_like_person(v)
        )
        return (hits / len(sample)) * 0.5
    if field in ("bio", "notes", "boardTitle"):
        hits = sum(1 for v in sample if len(v) > 8)
        return (hits / len(sample)) * 0.4
    return 0.0


def _detect_header_row(df: pd.DataFrame, max_scan: int = 8) -> tuple[int, float]:
    best_idx = 0
    best_score = -1.0
    limit = min(max_scan, len(df))
    for i in range(limit):
        score = sum(
            _header_score(_cell_str(cell), field)
            for cell in df.iloc[i].tolist()
            for field in FIELD_KEYWORDS
        )
        if score > best_score:
            best_score = score
            best_idx = i
    return best_idx, best_score


def _map_columns(df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, str], list[str]]:
    warnings: list[str] = []
    col_labels = [_cell_str(c) for c in df.columns]
    named_header_score = sum(
        _header_score(label, field) for label in col_labels for field in FIELD_KEYWORDS
    )
    # Se le colonne hanno già intestazioni utili (export HTML AIA), usale
    # senza cercare una riga-header nei dati (evita di mangiare la prima persona).
    if named_header_score >= 1.2 and not all(
        re.fullmatch(r"col\d+", label) for label in col_labels
    ):
        headers = col_labels
        body = df.copy()
    else:
        header_idx, header_score = _detect_header_row(df)
        if header_score >= 1.2:
            headers = [_cell_str(v) for v in df.iloc[header_idx].tolist()]
            body = df.iloc[header_idx + 1 :].copy()
            if header_idx > 0:
                warnings.append(f"Intestazioni rilevate alla riga {header_idx + 1}.")
        else:
            headers = [f"col{i}" for i in range(len(df.columns))]
            body = df.copy()
            warnings.append(
                "Intestazioni non chiare: colonne riconosciute dal contenuto."
            )

    body.columns = [f"col{i}" for i in range(len(body.columns))]
    mapping: dict[str, str] = {}
    used_fields: set[str] = set()
    used_cols: set[str] = set()

    header_assignments: list[tuple[float, str, str]] = []
    for i, header in enumerate(headers):
        col = body.columns[i] if i < len(body.columns) else f"col{i}"
        for field in FIELD_KEYWORDS:
            hs = _header_score(header, field)
            if hs >= 0.65:
                header_assignments.append((hs, field, col))
    header_assignments.sort(key=lambda x: x[0], reverse=True)
    for _, field, col in header_assignments:
        if field in used_fields or col in used_cols:
            continue
        mapping[field] = col
        used_fields.add(field)
        used_cols.add(col)

    content_assignments: list[tuple[float, str, str]] = []
    for col in body.columns:
        if col in used_cols:
            continue
        values = body[col].tolist()
        for field in FIELD_KEYWORDS:
            if field in used_fields:
                continue
            cs = _content_score(values, field)
            if cs >= 0.55:
                content_assignments.append((cs, field, col))
    content_assignments.sort(key=lambda x: x[0], reverse=True)
    for _, field, col in content_assignments:
        if field in used_fields or col in used_cols:
            continue
        mapping[field] = col
        used_fields.add(field)
        used_cols.add(col)

    renamed = body.rename(columns={v: k for k, v in mapping.items()}).copy()
    keep = [k for k in mapping]
    renamed = renamed[[c for c in keep if c in renamed.columns]]
    return renamed, mapping, warnings


def _normalize_member_role(raw: str, category: str = "") -> tuple[str, str, str]:
    text = _normalize_name_key(raw)
    cat = _normalize_name_key(category)
    observer_type = ""
    board_title = ""
    raw_u = _cell_str(raw).strip().upper()

    # Codici AIA ufficiali
    if raw_u == "AB" or "benemerito" in text or "benemerito" in cat:
        return "arbitro", "", ""
    if raw_u == "OA" or text == "oa":
        return "osservatore", "oa", ""
    if raw_u == "OT" or text == "ot":
        return "osservatore", "ot", ""
    # AA = Assistente Arbitrale (non aspirante)
    if raw_u == "AA":
        return "assistente", "", ""

    if (
        "consiglio" in text
        or "presidente" in text
        or "segretario" in text
        or "vice" in text
    ):
        role = "consiglio_direttivo"
        board_title = _cell_str(raw)
        if "presidente" in text and "vice" not in text:
            board_title = board_title or "Presidente"
    elif "osservatore" in text or "organo tecnico" in cat:
        role = "osservatore"
        observer_type = "ot" if "organo tecnico" in cat or "ot" in text else "oa"
    elif "assistente" in text or "tutor" in text:
        role = "assistente"
    else:
        role = "arbitro"

    if role not in MEMBER_ROLES:
        role = "arbitro"
    return role, observer_type, board_title


def _parse_year(value: str) -> Optional[int]:
    v = _cell_str(value)
    if not v:
        return None
    m = re.search(r"(19|20)\d{2}", v)
    if not m:
        return None
    y = int(m.group(0))
    if 1950 <= y <= datetime.now().year + 1:
        return y
    return None


def _row_from_mapped(
    row: dict[str, Any], line: int, warnings: list[str]
) -> Optional[dict]:
    first = row.get("firstName", "")
    last = row.get("lastName", "")
    full = row.get("fullName", "")
    if full and (not first or not last):
        first, last = _split_full_name(full)
    if not first and last:
        first, last = _split_full_name(last)
    first = _cell_str(first)
    last = _cell_str(last)
    if not first or not last:
        warnings.append(f"Riga {line}: nome/cognome mancanti — saltata.")
        return None

    role_raw = row.get("memberRole", "")
    category = _cell_str(row.get("category", ""))
    member_role, observer_type, board_title = _normalize_member_role(role_raw, category)
    if row.get("boardTitle"):
        board_title = _cell_str(row.get("boardTitle"))
    if row.get("observerType"):
        ot = _cell_str(row.get("observerType")).lower()
        if ot in ("oa", "ot"):
            observer_type = ot
    aia_code = _cell_str(role_raw).strip().upper()
    if aia_code not in {"AE", "AA", "AB", "OA", "OT", "AFR"}:
        aia_code = ""

    # AB: niente boardTitle generico; categoria massima solo AE/AA
    if board_title == "Arbitro Benemerito":
        board_title = ""
    if aia_code not in {"AE", "AA"}:
        category = ""

    email = _cell_str(row.get("email", ""))
    if email and not _looks_like_email(email):
        warnings.append(f"Riga {line}: email non valida — ignorata.")
        email = ""

    from .member_roles import (
        infer_organigramma_kind,
        is_section_president_title,
    )

    draft = {
        "firstName": first,
        "lastName": last,
        "memberRole": member_role,
        "observerType": observer_type,
        "boardTitle": board_title,
        "role": aia_code,
        "category": category,
    }
    organigramma_kind = infer_organigramma_kind(draft)
    is_president = is_section_president_title(board_title, organigramma_kind)

    return {
        "firstName": first,
        "lastName": last,
        "memberRole": member_role,
        "observerType": observer_type,
        "organigrammaKind": organigramma_kind,
        "boardTitle": board_title,
        "isPresident": is_president,
        "category": category,
        "role": aia_code,
        "meccanografico": _cell_str(row.get("meccanografico", "")),
        "email": email,
        "phone": _cell_str(row.get("phone", "")),
        "yearStart": _parse_year(row.get("yearStart", "")),
        "bio": _cell_str(row.get("bio", "")),
        "notes": _cell_str(row.get("notes", "")),
    }


def _member_dedup_key(row: dict) -> str:
    mec = (row.get("meccanografico") or "").strip().lower()
    if mec:
        return f"mec:{mec}"
    email = (row.get("email") or "").strip().lower()
    if email:
        return f"email:{email}"
    return f"name:{_normalize_name_key(row['firstName'])}|{_normalize_name_key(row['lastName'])}"


def _dedupe_rows(rows: list[dict]) -> tuple[list[dict], int]:
    seen: set[str] = set()
    out: list[dict] = []
    skipped = 0
    for row in rows:
        key = _member_dedup_key(row)
        if key in seen:
            skipped += 1
            continue
        seen.add(key)
        out.append(row)
    return out, skipped


def parse_members_file(
    content: bytes, filename: str
) -> tuple[list[dict], list[str], dict]:
    tables, file_type = extract_raw_tables(content, filename)
    warnings: list[str] = []
    mappings: list[dict] = []
    rows: list[dict] = []

    for raw_df in tables:
        if raw_df.empty:
            continue
        mapped_df, col_map, map_warnings = _map_columns(raw_df)
        warnings.extend(map_warnings)
        if col_map:
            mappings.append(col_map)

        for idx, raw in mapped_df.iterrows():
            line = int(idx) + 1
            row = {k: _cell_str(v) for k, v in raw.items()}
            parsed = _row_from_mapped(row, line, warnings)
            if parsed:
                rows.append(parsed)

    rows, dup_in_file = _dedupe_rows(rows)
    if dup_in_file:
        warnings.append(f"{dup_in_file} righe duplicate nel file ignorate.")

    meta = {"fileType": file_type, "tablesFound": len(tables), "columnMaps": mappings}
    if not rows:
        raise ValueError(
            "Nessun associato valido trovato. Servono almeno nome e cognome (o nominativo)."
        )
    return rows, warnings, meta


async def _unique_slug(db, first_name: str, last_name: str) -> str:
    base = slugify(f"{first_name}-{last_name}") or "associato"
    slug = base
    i = 1
    while await db.members.find_one({"slug": slug}, {"_id": 0, "id": 1}):
        i += 1
        slug = f"{base}-{i}"
    return slug


async def _find_existing_member(db, row: dict) -> Optional[dict]:
    mec = (row.get("meccanografico") or "").strip()
    if mec:
        found = await db.members.find_one({"meccanografico": mec}, {"_id": 0})
        if found:
            return found

    email = (row.get("email") or "").strip()
    if email:
        found = await db.members.find_one(
            {"email": {"$regex": f"^{re.escape(email)}$", "$options": "i"}},
            {"_id": 0},
        )
        if found:
            return found

    fn, ln = row["firstName"], row["lastName"]
    candidates = await db.members.find(
        {
            "firstName": {"$regex": f"^{re.escape(fn)}$", "$options": "i"},
            "lastName": {"$regex": f"^{re.escape(ln)}$", "$options": "i"},
        },
        {"_id": 0},
    ).to_list(20)
    target = _normalize_name_key(f"{fn} {ln}")
    for cand in candidates:
        if (
            _normalize_name_key(
                f"{cand.get('firstName', '')} {cand.get('lastName', '')}"
            )
            == target
        ):
            return cand
    return None


def _merge_member(existing: dict, incoming: dict) -> dict:
    """Aggiorna solo campi valorizzati nell'import; categoria mai obbligatoria."""
    out = {**existing}
    for key, val in incoming.items():
        if val is None:
            continue
        if isinstance(val, str) and not val.strip():
            continue
        if key == "yearStart" and val == "":
            continue
        out[key] = val
    out["updatedAt"] = datetime.now(timezone.utc).isoformat()
    return out


async def import_members_from_file(
    content: bytes,
    filename: str,
    *,
    dry_run: bool = False,
) -> dict:
    rows, parse_warnings, meta = parse_members_file(content, filename)
    db = get_db()
    batch_at = datetime.now(timezone.utc).isoformat()

    preview: list[dict] = []
    inserted = 0
    updated = 0
    skipped_duplicates = 0
    errors: list[str] = list(parse_warnings)

    for row in rows:
        existing = await _find_existing_member(db, row)
        is_update = existing is not None

        if len(preview) < 15:
            preview.append(
                {
                    "firstName": row["firstName"],
                    "lastName": row["lastName"],
                    "memberRole": row["memberRole"],
                    "category": row.get("category") or "",
                    "meccanografico": row.get("meccanografico") or "",
                    "existing": is_update,
                }
            )

        if dry_run:
            if is_update:
                skipped_duplicates += 1
            continue

        if existing:
            merged = _merge_member(existing, row)
            normalize_member(merged)
            await db.members.update_one({"id": existing["id"]}, {"$set": merged})
            from .portal_credentials import ensure_member_portal_credentials

            await ensure_member_portal_credentials(merged)
            updated += 1
            continue

        slug = await _unique_slug(db, row["firstName"], row["lastName"])
        member = Member(
            slug=slug,
            firstName=row["firstName"],
            lastName=row["lastName"],
            memberRole=row["memberRole"],
            observerType=row.get("observerType") or "",
            boardTitle=row.get("boardTitle") or "",
            isPresident=bool(row.get("isPresident")),
            category=row.get("category") or "",
            role=row.get("role") or "",
            yearStart=row.get("yearStart"),
            meccanografico=row.get("meccanografico") or "",
            email=row.get("email") or "",
            phone=row.get("phone") or "",
            bio=row.get("bio") or "",
            notes=row.get("notes") or "",
        )
        doc = member.model_dump()
        normalize_member(doc)
        await db.members.insert_one(doc.copy())
        from .portal_credentials import ensure_member_portal_credentials

        await ensure_member_portal_credentials(doc)
        inserted += 1

    if not dry_run:
        await db.site_settings.update_one(
            {"id": "site-settings"},
            {
                "$set": {
                    "lastMembersFileImport": {
                        "at": batch_at,
                        "filename": filename,
                        "fileType": meta.get("fileType"),
                        "rowsParsed": len(rows),
                        "inserted": inserted,
                        "updated": updated,
                        "warnings": errors[:30],
                    }
                }
            },
            upsert=True,
        )

    return {
        "ok": True,
        "dryRun": dry_run,
        "parsed": len(rows),
        "inserted": inserted,
        "updated": updated,
        "skippedDuplicates": skipped_duplicates,
        "preview": preview,
        "warnings": errors[:50],
        "filename": filename,
        "fileType": meta.get("fileType"),
        "tablesFound": meta.get("tablesFound"),
        "columnMaps": meta.get("columnMaps"),
    }
