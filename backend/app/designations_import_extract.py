"""Estrae tabelle grezze da CSV, Excel, PDF e Word per l'import designazioni."""
from __future__ import annotations

import io
import re
from typing import Any

import pandas as pd

SUPPORTED_EXTENSIONS = (".csv", ".xlsx", ".xls", ".xlsm", ".pdf", ".docx", ".doc")


def _cell_str(value: Any) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    text = str(value).strip()
    if text.lower() in ("nan", "none", "nat"):
        return ""
    return text


def _normalize_table(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [_cell_str(c) for c in df.columns]
    df = df.map(lambda v: _cell_str(v))
    df = df.replace("", pd.NA).dropna(how="all").fillna("")
    df = df.loc[:, ~(df.astype(str).eq("").all())]
    return df.reset_index(drop=True)


def _read_csv_bytes(content: bytes) -> pd.DataFrame:
    for encoding in ("utf-8-sig", "utf-8", "latin-1", "cp1252"):
        try:
            text = content.decode(encoding)
            break
        except UnicodeDecodeError:
            text = None
    if text is None:
        raise ValueError("Codifica file non supportata.")
    sep = ";" if text.count(";") >= text.count(",") else ","
    return pd.read_csv(io.StringIO(text), sep=sep, dtype=str, header=None)


def _read_excel_bytes(content: bytes) -> list[pd.DataFrame]:
    xls = pd.ExcelFile(io.BytesIO(content))
    out: list[pd.DataFrame] = []
    for sheet in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name=sheet, dtype=str, header=None)
        if not df.empty:
            out.append(df)
    return out


def _read_pdf_tables(content: bytes) -> list[pd.DataFrame]:
    try:
        import pdfplumber
    except ImportError as exc:
        raise ValueError("Supporto PDF non disponibile sul server.") from exc

    tables: list[pd.DataFrame] = []
    with pdfplumber.open(io.BytesIO(content)) as pdf:
        for page in pdf.pages:
            for table in page.extract_tables() or []:
                if not table or len(table) < 2:
                    continue
                header = [_cell_str(c) for c in table[0]]
                rows = [[_cell_str(c) for c in row] for row in table[1:]]
                if not any(header) and rows:
                    header = [f"col{i}" for i in range(len(rows[0]))]
                df = pd.DataFrame(rows, columns=header[: len(rows[0])] if rows else header)
                tables.append(df)
    return tables


def _read_docx_tables(content: bytes) -> list[pd.DataFrame]:
    try:
        from docx import Document
    except ImportError as exc:
        raise ValueError("Supporto Word non disponibile sul server.") from exc

    doc = Document(io.BytesIO(content))
    tables: list[pd.DataFrame] = []
    for table in doc.tables:
        rows = [[_cell_str(cell.text) for cell in row.cells] for row in table.rows]
        if len(rows) < 2:
            continue
        header = rows[0]
        body = rows[1:]
        if not any(header):
            header = [f"col{i}" for i in range(len(body[0]) if body else 0)]
        df = pd.DataFrame(body, columns=header[: len(body[0])] if body else header)
        tables.append(df)
    return tables


def _parse_text_lines_to_rows(text: str) -> pd.DataFrame:
    """Fallback: righe libere tipo «17/05/2026  Arbitro  Luca Bianchi  Casa - Ospite»."""
    rows: list[list[str]] = []
    for line in text.splitlines():
        line = re.sub(r"\s+", " ", line.strip())
        if len(line) < 12:
            continue
        date_m = re.search(r"\b(\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4}|\d{4}-\d{2}-\d{2})\b", line)
        if not date_m:
            continue
        rest = line[date_m.end() :].strip(" -|;\t")
        role_m = re.search(
            r"\b(arbitro|assistente\s*[12]?|assistente)\b",
            rest,
            flags=re.I,
        )
        gara_m = re.search(r"(.+?)\s+-\s+(.+?)(?:\s+\||\s{2,}|$)", rest)
        if role_m and gara_m:
            role = role_m.group(0)
            before = rest[: role_m.start()].strip()
            after = rest[role_m.end() :].strip()
            name = before or after.split("  ")[0].strip()
            rows.append([date_m.group(1), gara_m.group(0), role, name])
        elif role_m:
            parts = [p.strip() for p in re.split(r"\s{2,}|\|", rest) if p.strip()]
            name = parts[0] if parts else ""
            gara = parts[1] if len(parts) > 1 else ""
            rows.append([date_m.group(1), gara, role_m.group(0), name])
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows, columns=["data", "gara", "ruolo", "nominativo"])


def extract_raw_tables(content: bytes, filename: str) -> tuple[list[pd.DataFrame], str]:
    """Restituisce tabelle grezze e il tipo di file rilevato."""
    lower = (filename or "").lower()
    if lower.endswith((".xlsx", ".xls", ".xlsm")):
        return [_normalize_table(df) for df in _read_excel_bytes(content) if not df.empty], "excel"
    if lower.endswith(".csv"):
        return [_normalize_table(_read_csv_bytes(content))], "csv"
    if lower.endswith(".pdf"):
        tables = [_normalize_table(df) for df in _read_pdf_tables(content) if not df.empty]
        if tables:
            return tables, "pdf"
        try:
            import pdfplumber

            text_parts: list[str] = []
            with pdfplumber.open(io.BytesIO(content)) as pdf:
                for page in pdf.pages:
                    text_parts.append(page.extract_text() or "")
            text_df = _parse_text_lines_to_rows("\n".join(text_parts))
            if not text_df.empty:
                return [_normalize_table(text_df)], "pdf-text"
        except Exception:
            pass
        raise ValueError("Nessuna tabella leggibile nel PDF.")
    if lower.endswith((".docx", ".doc")):
        if lower.endswith(".doc"):
            raise ValueError("I file .doc legacy non sono supportati. Salva come .docx o PDF.")
        tables = [_normalize_table(df) for df in _read_docx_tables(content) if not df.empty]
        if tables:
            return tables, "word"
        raise ValueError("Nessuna tabella trovata nel documento Word.")
    raise ValueError("Formato non supportato. Usa CSV, Excel, PDF o Word (.docx).")
