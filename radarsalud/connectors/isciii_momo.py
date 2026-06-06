"""Conector ISCIII MoMo (mortalidad observada y esperada por provincia).

MoMo (Monitorización de la Mortalidad) del ISCIII publica un CSV abierto con la
mortalidad diaria observada y la esperada (modelo histórico) por ámbito
(nacional, comunidad autónoma y provincia), sexo y grupo de edad.

Es una fuente REAL, abierta y estructurada. El volcado completo es grande
(~700 MB), por lo que este conector:
  - hace streaming sin guardar el fichero entero,
  - pre-filtra líneas baratas (totales 'all' y meses recientes),
  - se queda solo con los totales provinciales de los últimos `days` días.

Por su coste, está marcado como `heavy=True` y se excluye de `ingest-all` salvo
que se pida explícitamente; siempre puede ejecutarse con
`radarsalud ingest --source isciii_momo`.

Fuente: https://momo.isciii.es/  (descarga: /public/momo/data)
Licencia: ISCIII, datos abiertos con cita de la fuente.
"""
from __future__ import annotations

import csv
import json
from datetime import datetime, timedelta

import httpx

from radarsalud.connectors.base import BaseConnector, ConnectorResult
from radarsalud.normalizers.geography import (
    PROVINCES_BY_CODE,
    centroid,
    community_for_province,
)
from radarsalud.utils.logging import get_logger

logger = get_logger(__name__)

MOMO_URL = "https://momo.isciii.es/public/momo/data"
DEFAULT_DAYS = 60


def _recent_month_prefixes(cutoff: datetime) -> set[str]:
    months: set[str] = set()
    d = cutoff.replace(day=1)
    end = datetime.utcnow()
    while d <= end:
        months.add(d.strftime("%Y-%m"))
        d = (d.replace(day=28) + timedelta(days=7)).replace(day=1)
    return months


class IsciiiMomoConnector(BaseConnector):
    name = "isciii_momo"
    category = "salud"
    source_type = "csv"
    operational = True
    heavy = True
    requires_key = False
    access_mode = "open"
    organization = "Instituto de Salud Carlos III (ISCIII) - MoMo"
    url = "https://momo.isciii.es/"
    license = "ISCIII - datos abiertos con cita de la fuente"

    def __init__(self, days: int = DEFAULT_DAYS) -> None:
        self.days = days

    def fetch(self) -> ConnectorResult:
        cutoff = datetime.utcnow() - timedelta(days=self.days)
        months = _recent_month_prefixes(cutoff)
        observations: list[dict] = []
        timeout = httpx.Timeout(connect=30.0, read=180.0, write=30.0, pool=30.0)
        headers = {"User-Agent": "RadarSalud/0.1 (+open-data research)"}

        try:
            with httpx.Client(timeout=timeout, follow_redirects=True, headers=headers) as client:
                with client.stream("GET", MOMO_URL) as resp:
                    if resp.status_code != 200:
                        return ConnectorResult(
                            status="failed",
                            message=f"MoMo respondió HTTP {resp.status_code}.",
                        )
                    observations = self._parse_stream(resp.iter_lines(), months, cutoff)
        except httpx.HTTPError as exc:
            logger.warning("MoMo sin acceso: %s", exc)
            return ConnectorResult(
                status="failed",
                message=f"Sin acceso de red a MoMo ({type(exc).__name__}).",
            )

        return ConnectorResult(
            observations=observations,
            status="success" if observations else "partial",
            message=(
                f"{len(observations)} observaciones de mortalidad provincial "
                f"(últimos {self.days} días) desde ISCIII MoMo."
            ),
        )

    @staticmethod
    def _parse_stream(lines, months: set[str], cutoff: datetime) -> list[dict]:
        observations: list[dict] = []
        it = iter(lines)
        header = next(it)
        cols = next(csv.reader([header]))
        idx = {name: i for i, name in enumerate(cols)}

        i_ambito = idx["ambito"]
        i_codine = idx["cod_ine_ambito"]
        i_nombre = idx["nombre_ambito"]
        i_sexo = idx["cod_sexo"]
        i_edad = idx["cod_gedad"]
        i_fecha = idx["fecha_defuncion"]
        i_obs = idx["defunciones_observadas"]
        i_base = idx["defunciones_estimadas_base"]
        i_q01 = idx["defunciones_estimadas_base_q01"]
        i_q99 = idx["defunciones_estimadas_base_q99"]

        for line in it:
            # Pre-filtro barato sobre la línea cruda.
            if '"all"' not in line:
                continue
            if not any(m in line for m in months):
                continue
            try:
                row = next(csv.reader([line]))
            except Exception:  # noqa: BLE001
                continue
            if row[i_ambito] != "provincia":
                continue
            if row[i_sexo] != "all" or row[i_edad] != "all":
                continue
            fecha = row[i_fecha]
            try:
                dt = datetime.strptime(fecha, "%Y-%m-%d")
            except ValueError:
                continue
            if dt < cutoff:
                continue

            code = _pad_code(row[i_codine])
            prov = PROVINCES_BY_CODE.get(code)
            province_name = prov.name if prov else row[i_nombre]
            coords = centroid(province_name) or (None, None)

            try:
                value = float(row[i_obs])
            except (ValueError, IndexError):
                continue
            payload = {
                "esperadas_base": _to_float(row[i_base]),
                "q01": _to_float(row[i_q01]),
                "q99": _to_float(row[i_q99]),
                "fuente": "ISCIII MoMo",
            }
            observations.append(
                {
                    "observed_at": dt,
                    "autonomous_community": community_for_province(province_name),
                    "province": province_name,
                    "province_code": code,
                    "latitude": coords[0],
                    "longitude": coords[1],
                    "signal_type": "mortalidad",
                    "health_event": "mortalidad",
                    "value": round(value, 2),
                    "unit": "defunciones",
                    "confidence_score": 0.9,
                    "normalized_payload_json": json.dumps(payload, ensure_ascii=False),
                }
            )
        return observations


def _pad_code(raw: str) -> str:
    raw = (raw or "").strip()
    try:
        return f"{int(raw):02d}"
    except ValueError:
        return raw


def _to_float(raw: str) -> float | None:
    try:
        return float(raw)
    except (TypeError, ValueError):
        return None
