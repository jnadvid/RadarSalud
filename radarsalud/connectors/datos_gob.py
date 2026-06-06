"""Conector para datos.gob.es (API abierta del catálogo nacional de datos).

datos.gob.es expone una API REST abierta y documentada (apidata / NTI-RISP) que
no requiere clave. Este conector busca datasets abiertos relacionados con salud
pública y guarda sus METADATOS (no asume que todos sean descargables).

Doc oficial: https://datos.gob.es/es/apidata
"""
from __future__ import annotations

from typing import Any

import httpx

from radarsalud.config import get_settings
from radarsalud.connectors.base import BaseConnector, ConnectorResult
from radarsalud.utils.http import polite_get
from radarsalud.utils.logging import get_logger

logger = get_logger(__name__)

# Términos de búsqueda de interés para vigilancia epidemiológica.
SEARCH_TERMS = [
    "gripe",
    "covid",
    "vigilancia epidemiologica",
    "aguas residuales",
    "calidad del aire",
    "temperatura",
    "mortalidad",
    "urgencias",
]


class DatosGobConnector(BaseConnector):
    name = "datos_gob_es"
    category = "salud"
    source_type = "api"
    operational = True
    requires_key = False
    access_mode = "open"
    organization = "datos.gob.es (Gobierno de España)"
    url = "https://datos.gob.es/es/apidata"
    license = "Variable por dataset (típicamente CC-BY / open data)"

    def fetch(self) -> ConnectorResult:
        base = get_settings().datos_gob_base_url.rstrip("/")
        metadata: list[dict[str, Any]] = []
        seen: set[str] = set()
        try:
            for term in SEARCH_TERMS:
                url = f"{base}/catalog/dataset/title/{httpx.URL(term).path or term}"
                try:
                    resp = polite_get(
                        url,
                        params={"_sort": "title", "_pageSize": 10, "_page": 0},
                        headers={"Accept": "application/json"},
                    )
                except httpx.HTTPError as exc:  # red no disponible: degradar con elegancia
                    logger.warning("datos.gob.es sin acceso para '%s': %s", term, exc)
                    return ConnectorResult(
                        status="failed",
                        message=f"Sin acceso de red a datos.gob.es ({exc}).",
                        source_metadata=metadata,
                    )
                if resp.status_code != 200:
                    logger.info("datos.gob.es término '%s' HTTP %s", term, resp.status_code)
                    continue
                items = _extract_items(resp.json())
                for item in items:
                    ds_id = item.get("identifier") or item.get("_about") or item.get("title")
                    if not ds_id or ds_id in seen:
                        continue
                    seen.add(str(ds_id))
                    metadata.append(
                        {
                            "term": term,
                            "title": _first(item.get("title")),
                            "identifier": ds_id,
                            "publisher": _first(item.get("publisher")),
                            "url": item.get("_about") or item.get("landingPage"),
                        }
                    )
        except Exception as exc:  # noqa: BLE001 - robustez de ingesta
            logger.exception("Error inesperado en datos.gob.es")
            return ConnectorResult(status="failed", message=str(exc),
                                   source_metadata=metadata)

        return ConnectorResult(
            status="success" if metadata else "partial",
            message=f"{len(metadata)} datasets de salud pública descubiertos en datos.gob.es.",
            source_metadata=metadata,
        )


def _extract_items(payload: Any) -> list[dict[str, Any]]:
    """Extrae la lista de resultados del JSON apidata (estructura variable)."""
    if isinstance(payload, dict):
        result = payload.get("result")
        if isinstance(result, dict):
            items = result.get("items")
            if isinstance(items, list):
                return items
        if isinstance(result, list):
            return result
        items = payload.get("items")
        if isinstance(items, list):
            return items
    if isinstance(payload, list):
        return payload
    return []


def _first(value: Any) -> Any:
    """apidata devuelve a menudo listas de literales multiidioma."""
    if isinstance(value, list) and value:
        first = value[0]
        if isinstance(first, dict):
            return first.get("_value") or first.get("value") or str(first)
        return first
    if isinstance(value, dict):
        return value.get("_value") or value.get("value")
    return value
