"""Importación de CSV local agregado (datos reales descargados manualmente).

No participa en `ingest-all` (necesita un fichero). Expone `parse_csv`, usado por
el servicio de importación, que valida fechas, provincias, valores numéricos,
eventos permitidos y AUSENCIA de datos personales antes de crear observaciones
con `data_mode = manual_import`.

Columnas aceptadas:
  observed_at, autonomous_community, province, municipality, signal_type,
  health_event, pathogen, value, unit, source_name
"""
from __future__ import annotations

from dataclasses import dataclass, field
from io import StringIO
from typing import Any

import pandas as pd

from radarsalud.connectors.base import BaseConnector, ConnectorResult
from radarsalud.normalizers.dates import parse_date
from radarsalud.normalizers.geography import (
    community_for_province,
    normalize_community,
    normalize_province,
    province_code,
)
from radarsalud.normalizers.units import normalize_unit
from radarsalud.utils.validation import (
    check_no_personal_columns,
    is_allowed_event,
    is_allowed_signal,
    looks_like_personal_data,
)

EXPECTED_COLUMNS = [
    "observed_at",
    "autonomous_community",
    "province",
    "municipality",
    "signal_type",
    "health_event",
    "pathogen",
    "value",
    "unit",
    "source_name",
]


@dataclass
class CsvParseResult:
    observations: list[dict[str, Any]] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    rows_total: int = 0

    @property
    def ok(self) -> bool:
        return not self.errors


def parse_csv(content: str) -> CsvParseResult:
    """Parsea y valida el contenido de un CSV agregado."""
    result = CsvParseResult()
    try:
        df = pd.read_csv(StringIO(content))
    except Exception as exc:  # noqa: BLE001
        result.errors.append(f"No se pudo leer el CSV: {exc}")
        return result

    # Rechazo temprano de columnas con datos personales.
    forbidden = check_no_personal_columns(list(df.columns))
    if forbidden:
        result.errors.append(
            f"El CSV contiene columnas no permitidas (posibles datos personales): {forbidden}"
        )
        return result

    if "observed_at" not in df.columns or "value" not in df.columns:
        result.errors.append("El CSV debe incluir al menos 'observed_at' y 'value'.")
        return result

    result.rows_total = len(df)
    for idx, row in df.iterrows():
        line = int(idx) + 2  # +2: cabecera + base 1

        observed_at = parse_date(row.get("observed_at"))
        if observed_at is None:
            result.errors.append(f"Fila {line}: fecha inválida en 'observed_at'.")
            continue

        raw_value = row.get("value")
        try:
            value = float(raw_value)
        except (TypeError, ValueError):
            result.errors.append(f"Fila {line}: 'value' no numérico ({raw_value!r}).")
            continue

        event = _clean(row.get("health_event"))
        if not is_allowed_event(event):
            result.errors.append(f"Fila {line}: evento no permitido ({event!r}).")
            continue
        signal = _clean(row.get("signal_type"))
        if not is_allowed_signal(signal):
            result.errors.append(f"Fila {line}: señal no permitida ({signal!r}).")
            continue

        # Comprobación heurística de datos personales en campos de texto libre.
        for col in ("municipality", "pathogen", "source_name"):
            val = _clean(row.get(col))
            if val and looks_like_personal_data(val):
                result.errors.append(
                    f"Fila {line}: posible dato personal en '{col}'. Importación rechazada."
                )
                break
        else:
            province = normalize_province(_clean(row.get("province")))
            community = normalize_community(_clean(row.get("autonomous_community")))
            if province and not community:
                community = community_for_province(province)
            result.observations.append(
                {
                    "observed_at": observed_at,
                    "autonomous_community": community,
                    "province": province,
                    "municipality": _clean(row.get("municipality")),
                    "province_code": province_code(province),
                    "signal_type": signal,
                    "health_event": event,
                    "pathogen": _clean(row.get("pathogen")),
                    "value": value,
                    "unit": normalize_unit(_clean(row.get("unit"))),
                    "source_name": _clean(row.get("source_name")),
                    "confidence_score": 0.8,  # dato real cargado manualmente
                }
            )
    return result


def _clean(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, float) and pd.isna(value):
        return None
    text = str(value).strip()
    return text or None


class CsvLocalConnector(BaseConnector):
    name = "csv_local"
    category = "otro"
    source_type = "csv"
    operational = False  # requiere un fichero; no participa en ingest-all
    access_mode = "manual_download"
    organization = "Importación manual"
    url = None
    license = "Según fuente original del CSV"

    def fetch(self) -> ConnectorResult:
        return ConnectorResult(
            status="skipped",
            message=(
                "csv_local: use `radarsalud import-csv FICHERO` o el endpoint "
                "POST /api/v1/uploads/csv para importar datos reales agregados."
            ),
        )
