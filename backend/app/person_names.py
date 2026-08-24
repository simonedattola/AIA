"""Formattazione nomi persona (es. MARIO ROSSI → Mario Rossi)."""

from __future__ import annotations


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
    if "'" in w:
        parts = w.split("'")
        return "'".join(
            (parts[0][:1].upper() + parts[0][1:].lower()) if parts[0] else ""
            if i == 0
            else _title_word(p)
            for i, p in enumerate(parts)
        )
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
