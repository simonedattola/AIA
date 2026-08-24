"""Sigle campionato AIA → etichetta leggibile per import designazioni."""

from __future__ import annotations

import re
import unicodedata

# Sigle tipiche dei file interni di sezione (Cat. / Categoria).
CHAMPIONSHIP_CODES: dict[str, str] = {
    # Campionati adulti
    "PRI": "Prima Categoria",
    "SEC": "Seconda Categoria",
    "TER": "Terza Categoria",
    # Femminile
    "FED": "Calcio Femminile Eccellenza",
    "FEP": "Calcio Femminile Promozione",
    "FCR": "Femminile Coppa Eccellenza Regionale",
    "ARF": "Under 17 Regionali Calcio a 11 Femminile",
    "GIF": "Under 15 Regionali Calcio a 11 Femminile",
    # Coppe
    "CP1": "Coppa Provincia",
    "CR2": "Coppa Regionale Seconda Categoria",
    "CRJ": "Coppa Regione Juniores",
    "CGB": "Under 14 Coppa Regionale Calcio a 11 Maschile",
    # Juniores
    "JUR": "Juniores Regionali",
    "JRB": "Juniores Regionale Fascia B",
    "JUP": "Juniores Provinciali",
    # Settore giovanile maschile
    "R18": "Under 18 Regionale Maschile Calcio a 11",
    "ALR": "Under 17 Regionali Calcio a 11 Maschile",
    "ALP": "Under 17 Provinciali Calcio a 11 Maschile",
    "ARB": "Under 16 Regionali Calcio a 11 Maschile",
    "ALB": "Under 16 Provinciali Calcio a 11 Maschile",
    "GIR": "Under 15 Regionali Calcio a 11 Maschile",
    "GIP": "Under 15 Provinciali Calcio a 11 Maschile",
    "GRB": "Under 14 Regionali Calcio a 11 Maschile",
    "GIB": "Under 14 Provinciali Calcio a 11 Maschile",
    # Amichevoli LND
    "ECC": "Amichevole LND Eccellenza",
    "PRO": "Amichevole LND Promozione",
    "JUN": "Amichevole LND Juniores Nazionali",
    "GIN": "Amichevole LND Giovanissimi Nazionali",
    "ALA": "Amichevole LND Campionato Nazionale Under 17 Serie A-B",
}

# Codice AIA in colonna Att. → ruolo designazione
AIA_ATT_ROLE_CODES: dict[str, str] = {
    "AE": "Arbitro",
    "AR": "Arbitro",
    "AA": "Assistente 1",
    "AA1": "Assistente 1",
    "AA2": "Assistente 2",
    "AB": "Arbitro",
    "AFR": "Arbitro",
    "OA": "Osservatore",
    "OT": "Osservatore",
}


def _strip_accents(text: str) -> str:
    text = unicodedata.normalize("NFKD", text or "")
    return "".join(c for c in text if not unicodedata.combining(c))


def normalize_championship_code(value: str | None) -> str:
    """Normalizza una cella Cat./Categoria o Att. a sigla uppercase (es. 'aa1' → 'AA1')."""
    raw = _strip_accents(str(value or "")).strip().upper()
    if not raw:
        return ""
    # Sigle ruolo tipo AA1/AA2: tenere lettere+cifre intere
    compact = re.sub(r"[^A-Z0-9]+", "", raw)
    if compact in AIA_ATT_ROLE_CODES or compact in CHAMPIONSHIP_CODES:
        return compact
    token = re.split(r"[\s/|_·.-]+", raw)[0]
    return token


def expand_championship_label(value: str | None) -> str:
    """
    Espande sigle note (SEC → Seconda Categoria).
    Se non è una sigla nota, restituisce il testo originale pulito.
    """
    raw = str(value or "").strip()
    if not raw:
        return ""
    code = normalize_championship_code(raw)
    if code in CHAMPIONSHIP_CODES and (
        re.sub(r"[^A-Za-z0-9]+", "", raw).upper() == code
        or len(raw) <= 4
        or raw.upper().startswith(code)
    ):
        if (
            re.fullmatch(r"[A-Za-z0-9]{2,4}", raw.strip())
            or re.sub(r"[^A-Za-z0-9]+", "", raw).upper() == code
        ):
            return CHAMPIONSHIP_CODES[code]
        rest = raw[len(code) :].lstrip(" -_/·.|")
        label = CHAMPIONSHIP_CODES[code]
        return f"{label} {rest}".strip() if rest else label
    return raw


def resolve_att_role(value: str | None) -> str | None:
    """Converte codice Att. AIA (AE/AR/AA1/AA2/…) in ruolo, oppure None."""
    code = normalize_championship_code(value)
    return AIA_ATT_ROLE_CODES.get(code)
