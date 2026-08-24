"""Import designazioni flessibile da file eterogenei (CSV, Excel, PDF, Word)."""

from __future__ import annotations

import hashlib
import re
import unicodedata
from datetime import datetime
from typing import Any, Optional

import pandas as pd

from .db import get_db
from .models import _id
from .championship_codes import expand_championship_label, resolve_att_role
from .designations_sync import (
    _build_member_lookup,
    _designation_match_key,
    _lookup_member_info,
    _normalize_name,
    _now,
    _resolve_member,
)
from .designations_import_extract import (
    SUPPORTED_EXTENSIONS,
    extract_raw_tables,
    _cell_str,
)
from .member_roles import is_observer_designation_role
from .scrapers.aia_lombardia import ROLE_MAP, _clean_text

SOURCE = "file-import"

# Keyword fuzzy matching. Prefer exact/longer tokens; short aliases are listed
# explicitly so "Cat." / "Gir." / "Att." from export AIA mappano correttamente.
FIELD_KEYWORDS: dict[str, list[str]] = {
    "matchDate": [
        "data ora",
        "data / ora",
        "data",
        "date",
        "when",
        "match date",
    ],
    "championship": [
        "campionato",
        "categoria",
        "category",
        "competizione",
        "livello",
        "torneo",
        "cat",
    ],
    "girone": ["girone", "giron", "gir", "group", "gruppo"],
    "matchDay": ["giornata", "giorn", "turno", "matchday", "round"],
    "matchHome": [
        "squadra locale",
        "sq locale",
        "squadra casa",
        "casa",
        "home",
        "domicilio",
        "match home",
        "locale",
    ],
    "matchAway": [
        "squadra ospite",
        "sq ospite",
        "ospite",
        "away",
        "trasferta",
        "match away",
        "visit",
    ],
    "matchLabel": [
        "partita",
        "incontro",
        "avversari",
        "squadre",
        "teams",
        "match",
        "gara",
    ],
    # Consuma "Num. Gara" senza usarlo come matchLabel
    "matchNumber": ["num gara", "numero gara", "n gara", "codice gara"],
    "venue": ["impianto", "campo", "stadio", "venue"],
    "role": [
        "ruolo",
        "role",
        "incarico",
        "designazione",
        "funzione",
        "att",
        "qualifica",
    ],
    "memberName": [
        "associato",
        "nominativo",
        "arbitro",
        "nome cognome",
        "nome e cognome",
        "ufficiale",
        "designato",
        "referee",
        "cognome",
        "nome",
        "name",
    ],
    "meccanografico": ["meccanografico", "matricola", "codice", "mec", "cod"],
    # Colonne da ignorare (Formato A: voti/rimborsi) — mappate per non rubare altri campi
    "ignored": [
        "ris",
        "risultato",
        "voto oa",
        "voto ot",
        "voto",
        "stato",
        "rimb",
        "rimborso",
    ],
}

IMPORT_TEMPLATE_CSV = (
    "data;cat.;gir.;giorn.;squadra locale;squadra ospite;att.;associato\r\n"
    "2026-05-17;SEC;R;1;PRO JUVENTUTE ASD;MAZZO 80 A.C.;AE;Menapace Lorenzo\r\n"
    "2026-05-17;SEC;R;1;PRO JUVENTUTE ASD;MAZZO 80 A.C.;AA;Rossi Marco\r\n"
)


def _strip_accents(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    return "".join(c for c in text if not unicodedata.combining(c))


def _norm_label(text: str) -> str:
    text = _strip_accents(_cell_str(text).lower())
    return re.sub(r"[^a-z0-9]+", " ", text).strip()


def _header_score(label: str, field: str) -> float:
    """Score header→field. Avoid short-token false positives (es. girone 'R')."""
    norm = _norm_label(label)
    if not norm:
        return 0.0
    best = 0.0
    for kw in FIELD_KEYWORDS.get(field, []):
        kn = _norm_label(kw)
        if not kn:
            continue
        if norm == kn:
            best = max(best, 1.0)
            continue
        # Substring match solo se entrambi hanno lunghezza sufficiente
        if len(kn) >= 3 and len(norm) >= 2 and (kn in norm or norm in kn):
            # Penalizza match troppo generici tipo "gara" in "num gara" per matchLabel
            if field == "matchLabel" and ("num" in norm or "numero" in norm or "n " in f" {norm} "):
                continue
            best = max(best, 0.9 if kn in norm else 0.85)
            continue
        tokens = [tok for tok in kn.split() if len(tok) >= 3]
        if tokens and any(tok in norm.split() for tok in tokens):
            best = max(best, 0.65)
    return best


def _looks_like_date(value: str) -> bool:
    return _parse_date(value) is not None


def _looks_like_role(value: str) -> bool:
    if resolve_att_role(value):
        return True
    key = _normalize_name(value)
    return key in ROLE_MAP or "assistente" in key or key == "arbitro"


def _looks_like_person(value: str) -> bool:
    text = _cell_str(value)
    if not text or len(text) < 4 or len(text) > 60:
        return False
    if _looks_like_role(text) or _looks_like_date(text):
        return False
    if " - " in text or re.search(r"\d{3,}", text):
        return False
    parts = text.split()
    return len(parts) >= 2 and all(p[:1].isalpha() for p in parts[:3])


def _looks_like_match(value: str) -> bool:
    text = _cell_str(value).lower()
    return bool(text and (" - " in text or " – " in text or " vs " in text))


def _looks_like_team(value: str) -> bool:
    text = _cell_str(value)
    if (
        not text
        or _looks_like_person(text)
        or _looks_like_role(text)
        or _looks_like_date(text)
    ):
        return False
    return len(text) >= 3 and not _looks_like_match(text)


def _content_score(values: list[str], field: str) -> float:
    if not values:
        return 0.0
    sample = [v for v in values if v][:25]
    if not sample:
        return 0.0
    if field == "matchDate":
        hits = sum(1 for v in sample if _looks_like_date(v))
        return hits / len(sample)
    if field == "role":
        hits = sum(1 for v in sample if _looks_like_role(v))
        return hits / len(sample)
    if field == "memberName":
        hits = sum(1 for v in sample if _looks_like_person(v))
        return hits / len(sample)
    if field == "matchLabel":
        hits = sum(1 for v in sample if _looks_like_match(v))
        return hits / len(sample)
    if field in ("matchHome", "matchAway"):
        hits = sum(1 for v in sample if _looks_like_team(v))
        return hits / len(sample)
    if field == "meccanografico":
        hits = sum(1 for v in sample if re.fullmatch(r"[A-Za-z0-9./-]{3,12}", v))
        return hits / len(sample)
    if field in ("championship", "girone", "matchDay"):
        hits = sum(1 for v in sample if 1 <= len(v) <= 40 and not _looks_like_person(v))
        return (hits / len(sample)) * 0.4
    return 0.0


def _detect_header_row(df: pd.DataFrame, max_scan: int = 8) -> tuple[int, float]:
    best_idx = 0
    best_score = -1.0
    limit = min(max_scan, len(df))
    for i in range(limit):
        row = df.iloc[i].tolist()
        score = 0.0
        for cell in row:
            for field in FIELD_KEYWORDS:
                score += _header_score(_cell_str(cell), field)
        if score > best_score:
            best_score = score
            best_idx = i
    return best_idx, best_score


def _map_columns(df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, str], list[str]]:
    """Mappa colonne per intestazioni e/o contenuto. L'ordine non conta."""
    warnings: list[str] = []
    header_idx, header_score = _detect_header_row(df)

    if header_score >= 1.5:
        headers = [_cell_str(v) for v in df.iloc[header_idx].tolist()]
        body = df.iloc[header_idx + 1 :].copy()
        if header_idx > 0:
            warnings.append(f"Intestazioni rilevate alla riga {header_idx + 1}.")
    else:
        headers = [f"col{i}" for i in range(len(df.columns))]
        body = df.copy()
        warnings.append("Intestazioni non chiare: colonne riconosciute dal contenuto.")

    body.columns = [f"col{i}" for i in range(len(body.columns))]

    mapping: dict[str, str] = {}
    used_fields: set[str] = set()
    used_cols: set[str] = set()

    # Fase 1: intestazioni esplicite (ordine colonne irrilevante)
    header_assignments: list[tuple[float, str, str]] = []
    for i, header in enumerate(headers):
        col = body.columns[i] if i < len(body.columns) else f"col{i}"
        for field in FIELD_KEYWORDS:
            hs = _header_score(header, field)
            if hs >= 0.65:
                header_assignments.append((hs, field, col))
    header_assignments.sort(key=lambda x: x[0], reverse=True)
    for hs, field, col in header_assignments:
        if field in used_fields or col in used_cols:
            continue
        mapping[field] = col
        used_fields.add(field)
        used_cols.add(col)

    # Fase 2: colonne rimanenti dal contenuto
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
    for cs, field, col in content_assignments:
        if field in used_fields or col in used_cols:
            continue
        mapping[field] = col
        used_fields.add(field)
        used_cols.add(col)

    required = {"matchDate", "memberName", "role"}
    if "matchLabel" not in mapping and not ({"matchHome", "matchAway"} <= used_fields):
        # prova a inferire gara da colonne non mappate
        for col in body.columns:
            if col in used_cols:
                continue
            if _content_score(body[col].tolist(), "matchLabel") >= 0.5:
                mapping["matchLabel"] = col
                used_cols.add(col)
                break

    missing = required - set(mapping.keys())
    if missing and not ({"matchHome", "matchAway"} <= set(mapping.keys())):
        warnings.append(
            "Alcune colonne non riconosciute automaticamente: "
            + ", ".join(sorted(missing))
            + ". Verifica l'anteprima."
        )

    renamed = body.rename(columns={v: k for k, v in mapping.items()}).copy()
    keep = [
        k
        for k in mapping
        if k not in ("ignored", "matchNumber", "venue")
    ]
    for k in (
        "matchLabel",
        "matchHome",
        "matchAway",
        "championship",
        "girone",
        "matchDay",
        "meccanografico",
        "role",
        "memberName",
        "matchDate",
    ):
        if k in renamed.columns and k not in keep:
            keep.append(k)
    renamed = renamed[[c for c in keep if c in renamed.columns]]
    return renamed, mapping, warnings


def _parse_date(value: str) -> Optional[str]:
    v = _cell_str(value)
    if not v:
        return None
    if re.fullmatch(r"\d+(\.\d+)?", v):
        try:
            serial = float(v)
            dt = pd.to_datetime(serial, unit="D", origin="1899-12-30")
            return dt.strftime("%Y-%m-%d")
        except (ValueError, OverflowError, TypeError):
            pass
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y", "%Y/%m/%d", "%d/%m/%y"):
        chunk = v[:10]
        try:
            return datetime.strptime(chunk, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    try:
        parsed = pd.to_datetime(v, dayfirst=True, errors="coerce")
        if pd.notna(parsed):
            return parsed.strftime("%Y-%m-%d")
    except (ValueError, TypeError):
        pass
    return None


def _normalize_role(role: str) -> str:
    att = resolve_att_role(role)
    if att:
        return att
    key = _normalize_name(role)
    if key in ROLE_MAP:
        return ROLE_MAP[key]
    if key == "assistente":
        return "Assistente 1"
    cleaned = _clean_text(role)
    return cleaned or "Arbitro"


def _split_match_label(label: str) -> tuple[str, str]:
    text = _cell_str(label)
    if not text:
        return "", ""
    for sep in (" - ", " – ", " — ", " vs ", " VS "):
        if sep in text:
            home, away = text.split(sep, 1)
            return home.strip(), away.strip()
    return text, ""


def _to_iso_datetime(date_str: str) -> str:
    if "T" in date_str:
        return date_str
    return f"{date_str}T12:00:00+00:00"


def _row_dict_from_mapped(
    row: dict[str, Any], line: int, warnings: list[str]
) -> Optional[dict]:
    match_date = _parse_date(row.get("matchDate", ""))
    if not match_date:
        warnings.append(f"Riga {line}: data non valida — saltata.")
        return None

    match_home = row.get("matchHome", "")
    match_away = row.get("matchAway", "")
    match_label = row.get("matchLabel", "")
    if match_label and (not match_home or not match_away):
        home, away = _split_match_label(match_label)
        match_home = match_home or home
        match_away = match_away or away
    if not match_label and match_home and match_away:
        match_label = f"{match_home} - {match_away}"
    if not match_label and not (match_home and match_away):
        warnings.append(f"Riga {line}: gara non indicata — saltata.")
        return None

    member_name = row.get("memberName", "")
    if not member_name:
        warnings.append(f"Riga {line}: nominativo mancante — saltata.")
        return None

    role_raw = row.get("role", "")
    role = _normalize_role(role_raw or "Arbitro")
    if is_observer_designation_role(role):
        warnings.append(f"Riga {line}: ruolo Osservatore — saltata.")
        return None

    championship = expand_championship_label(row.get("championship", ""))

    return {
        "matchDate": match_date,
        "championship": championship,
        "girone": row.get("girone", ""),
        "matchDay": row.get("matchDay", ""),
        "matchHome": match_home,
        "matchAway": match_away,
        "matchLabel": match_label,
        "category": championship,
        "role": role,
        "memberName": member_name,
        "meccanografico": row.get("meccanografico", ""),
        "status": "published",
        "source": SOURCE,
    }


def _dedupe_rows(rows: list[dict]) -> tuple[list[dict], int]:
    seen: set[str] = set()
    out: list[dict] = []
    skipped = 0
    for row in rows:
        key = _designation_match_key(
            {**row, "matchDate": _to_iso_datetime(row["matchDate"])}
        )
        if key in seen:
            skipped += 1
            continue
        seen.add(key)
        out.append(row)
    return out, skipped


def parse_designations_file(
    content: bytes, filename: str
) -> tuple[list[dict], list[str], dict]:
    """Estrae e normalizza righe da qualsiasi formato supportato."""
    tables, file_type = extract_raw_tables(content, filename)
    warnings: list[str] = []
    mappings: list[dict] = []
    rows: list[dict] = []

    for t_idx, raw_df in enumerate(tables):
        if raw_df.empty:
            continue
        mapped_df, col_map, map_warnings = _map_columns(raw_df)
        warnings.extend(map_warnings)
        if col_map:
            mappings.append(col_map)

        for idx, raw in mapped_df.iterrows():
            line = int(idx) + 1
            row = {k: _cell_str(v) for k, v in raw.items()}
            parsed = _row_dict_from_mapped(row, line, warnings)
            if parsed:
                rows.append(parsed)

    rows, dup_in_file = _dedupe_rows(rows)
    if dup_in_file:
        warnings.append(f"{dup_in_file} righe duplicate nel file ignorate.")

    meta = {"fileType": file_type, "tablesFound": len(tables), "columnMaps": mappings}
    if not rows:
        raise ValueError(
            "Nessuna designazione valida trovata. Il file è stato letto ma non è stato possibile "
            "riconoscere data, gara e nominativo."
        )
    return rows, warnings, meta


async def _resolve_member_for_import(
    db,
    full_name: str,
    meccanografico: str,
    designation_role: str,
    member_lookup: dict[str, dict],
    *,
    allow_create: bool = True,
) -> tuple[Optional[str], str, bool, str]:
    """Return (memberId, memberSlug, created, canonicalMemberName)."""
    mec = (meccanografico or "").strip()
    if mec:
        key = f"mec:{mec.lower()}"
        if key in member_lookup:
            info = member_lookup[key]
            canonical = f"{info.get('firstName', '')} {info.get('lastName', '')}".strip() or full_name
            return info["id"], info.get("slug", ""), False, canonical

    existing = _lookup_member_info(member_lookup, full_name)
    if existing:
        canonical = (
            f"{existing.get('firstName', '')} {existing.get('lastName', '')}".strip()
            or full_name
        )
        return existing["id"], existing.get("slug", ""), False, canonical

    if not allow_create:
        return None, "", False, full_name

    # Export Associato = Cognome Nome: in creazione usa quell'ordine
    member_id, member_slug, created = await _resolve_member(
        db,
        full_name,
        designation_role,
        member_lookup,
        surname_first=True,
    )
    if created:
        info = _lookup_member_info(member_lookup, full_name) or {}
        canonical = (
            f"{info.get('firstName', '')} {info.get('lastName', '')}".strip() or full_name
        )
        return member_id, member_slug, True, canonical
    return member_id, member_slug, False, full_name


async def _find_existing_by_match_key(db, doc_fields: dict) -> Optional[dict]:
    """Cerca duplicati su tutte le fonti (manuale, file, AIA)."""
    target = _designation_match_key(doc_fields)
    md = (doc_fields.get("matchDate") or "")[:10]
    name = doc_fields.get("memberName") or ""
    query: dict = {}
    if md:
        query["matchDate"] = {"$regex": f"^{re.escape(md)}"}
    if name:
        query["memberName"] = {"$regex": re.escape(name.strip()), "$options": "i"}

    candidates = await db.designations.find(query, {"_id": 0}).to_list(200)
    for cand in candidates:
        if _designation_match_key(cand) == target:
            return cand
    return None


def _file_import_external_id(doc: dict) -> str:
    key = _designation_match_key(doc)
    return hashlib.sha256(f"{SOURCE}|{key}".encode("utf-8")).hexdigest()[:32]


async def import_designations_from_file(
    content: bytes,
    filename: str,
    *,
    dry_run: bool = False,
) -> dict:
    rows, parse_warnings, meta = parse_designations_file(content, filename)
    db = get_db()
    member_lookup = await _build_member_lookup(db)
    batch_at = _now()

    preview: list[dict] = []
    inserted = 0
    updated = 0
    skipped_duplicates = 0
    members_created = 0
    unlinked = 0
    errors: list[str] = list(parse_warnings)

    for row in rows:
        member_id, member_slug, created, canonical_name = await _resolve_member_for_import(
            db,
            row["memberName"],
            row.get("meccanografico", ""),
            row["role"],
            member_lookup,
            allow_create=not dry_run,
        )
        linked = bool(member_id)
        would_create = not linked and bool(_normalize_name(row["memberName"]))
        if created:
            members_created += 1
        if not linked and not would_create:
            unlinked += 1

        display_name = canonical_name if linked or created else row["memberName"]

        doc_fields = {
            "matchDate": _to_iso_datetime(row["matchDate"]),
            "championship": row.get("championship", ""),
            "girone": row.get("girone", ""),
            "matchDay": row.get("matchDay", ""),
            "matchHome": row.get("matchHome", ""),
            "matchAway": row.get("matchAway", ""),
            "matchLabel": row.get("matchLabel", ""),
            "category": row.get("category", "") or row.get("championship", ""),
            "role": row["role"],
            "memberName": display_name,
            "memberId": member_id,
            "memberSlug": member_slug or "",
            "status": row.get("status", "published"),
            "source": SOURCE,
            "externalId": _file_import_external_id(
                {
                    **row,
                    "memberName": display_name,
                    "matchDate": _to_iso_datetime(row["matchDate"]),
                }
            ),
            "importedAt": batch_at,
            "lastSeenAt": batch_at,
        }

        if len(preview) < 15:
            preview.append(
                {
                    "matchDate": row["matchDate"],
                    "matchLabel": doc_fields["matchLabel"],
                    "role": row["role"],
                    "memberName": display_name,
                    "linked": linked,
                    "wouldCreate": would_create and dry_run,
                }
            )

        if dry_run:
            existing = await _find_existing_by_match_key(db, doc_fields)
            if existing:
                skipped_duplicates += 1
            continue

        existing = await _find_existing_by_match_key(db, doc_fields)
        if existing:
            # Aggiorna la designazione esistente senza crearne una seconda
            preserve = {
                "id": existing["id"],
                "createdAt": existing.get("createdAt"),
                "source": existing.get("source") or SOURCE,
            }
            merged = {**doc_fields, **preserve}
            await db.designations.update_one({"id": existing["id"]}, {"$set": merged})
            updated += 1
            continue

        doc = {"id": _id(), "createdAt": batch_at, **doc_fields}
        await db.designations.insert_one(doc)
        inserted += 1

    if not dry_run:
        await db.site_settings.update_one(
            {"id": "site-settings"},
            {
                "$set": {
                    "lastDesignationsFileImport": {
                        "at": batch_at,
                        "filename": filename,
                        "fileType": meta.get("fileType"),
                        "rowsParsed": len(rows),
                        "inserted": inserted,
                        "updated": updated,
                        "skippedDuplicates": skipped_duplicates,
                        "membersCreated": members_created,
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
        "membersCreated": members_created,
        "unlinked": unlinked,
        "preview": preview,
        "warnings": errors[:50],
        "filename": filename,
        "fileType": meta.get("fileType"),
        "tablesFound": meta.get("tablesFound"),
        "columnMaps": meta.get("columnMaps"),
    }
