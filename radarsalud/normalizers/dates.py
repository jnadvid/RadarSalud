"""Normalización de fechas a datetime, tolerante con formatos habituales."""
from __future__ import annotations

from datetime import date, datetime

import pandas as pd

_KNOWN_FORMATS = (
    "%Y-%m-%d",
    "%d/%m/%Y",
    "%d-%m-%Y",
    "%Y/%m/%d",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%d %H:%M:%S",
    "%d/%m/%Y %H:%M",
)


def parse_date(value: object) -> datetime | None:
    """Convierte un valor heterogéneo a datetime, o None si no es válido."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return datetime(value.year, value.month, value.day)
    text = str(value).strip()
    if not text or text.lower() in {"nan", "nat", "none", "null"}:
        return None
    for fmt in _KNOWN_FORMATS:
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    # Último recurso: pandas, sin lanzar excepción.
    parsed = pd.to_datetime(text, errors="coerce", dayfirst=True)
    if pd.isna(parsed):
        return None
    return parsed.to_pydatetime()


def to_iso(value: datetime | None) -> str | None:
    return value.isoformat() if value else None
