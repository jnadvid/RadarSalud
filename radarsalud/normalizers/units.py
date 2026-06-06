"""Normalización ligera de unidades y nombres de unidad."""
from __future__ import annotations

_UNIT_ALIASES = {
    "casos": "casos",
    "n_casos": "casos",
    "numero_casos": "casos",
    "incidencia": "tasa_100k",
    "tasa": "tasa_100k",
    "tasa_100000": "tasa_100k",
    "por_100000": "tasa_100k",
    "celsius": "°C",
    "c": "°C",
    "ºc": "°C",
    "grados": "°C",
    "ugm3": "µg/m³",
    "ug/m3": "µg/m³",
    "µg/m3": "µg/m³",
    "porcentaje": "%",
    "pct": "%",
}


def normalize_unit(unit: str | None) -> str | None:
    if not unit:
        return None
    key = unit.strip().lower()
    return _UNIT_ALIASES.get(key, unit.strip())
