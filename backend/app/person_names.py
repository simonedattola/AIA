"""Formattazione nomi persona (es. MARIO ROSSI → Mario Rossi)."""

from __future__ import annotations

_APOSTROPHES = ("'", "\u2019", "\u2018", "`")


def _title_word(word: str) -> str:
    w = (word or "").strip()
    if not w:
        return ""
    if " " in w:
        return " ".join(_title_word(part) for part in w.split() if part.strip())
    if len(w) == 1:
        return w.upper()
    if "-" in w:
        return "-".join(_title_word(part) for part in w.split("-"))
    for mark in _APOSTROPHES:
        if mark in w:
            # Normalizza a apostrofo ASCII; title-case ogni segmento.
            # Es. D'AZZEO → D'Azzeo, DELL'ACQUA → Dell'Acqua, IANNO' → Ianno'
            parts = w.replace(mark, "'").split("'")
            return "'".join(_title_word(p) if p else "" for p in parts)
    return w[0].upper() + w[1:].lower()


def format_person_name(
    first: str | None = None, last: str | None = None, *, full: str | None = None
) -> str:
    """Nome Cognome in title case (es. «Mario Rossi»)."""
    if full and not (first or last):
        return " ".join(_title_word(p) for p in full.split() if p.strip())
    fn = _title_word(first or "")
    ln = _title_word(last or "")
    return f"{fn} {ln}".strip()


def format_person_name_parts(first: str | None, last: str | None) -> tuple[str, str]:
    return _title_word(first or ""), _title_word(last or "")


def apply_title_case_to_person(doc: dict) -> bool:
    """Normalizza firstName/lastName in «Nome Cognome». Ritorna True se ha modificato."""
    first, last = format_person_name_parts(doc.get("firstName"), doc.get("lastName"))
    changed = False
    if first and doc.get("firstName") != first:
        doc["firstName"] = first
        changed = True
    if last and doc.get("lastName") != last:
        doc["lastName"] = last
        changed = True
    display = format_person_name(first, last)
    if display and doc.get("displayName") != display:
        doc["displayName"] = display
        changed = True
    return changed
