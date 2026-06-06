"""Conector paraguas de comunidades autónomas (lee el catálogo por CCAA).

No ingiere datos automáticamente en el MVP: documenta y expone el catálogo de
portales autonómicos definido en `data/sources_catalog.yml`. La ingesta concreta
de cada portal (Socrata, CKAN, CSV...) queda como trabajo futuro verificable.
"""
from __future__ import annotations

from radarsalud.connectors.base import BaseConnector, ConnectorResult
from radarsalud.connectors.catalog import load_catalog


class ComunidadesAutonomasConnector(BaseConnector):
    name = "comunidades_autonomas"
    category = "salud"
    source_type = "html"
    operational = False
    access_mode = "pending_verification"
    organization = "Comunidades Autónomas (varios)"
    url = None
    license = "Variable por comunidad"

    def fetch(self) -> ConnectorResult:
        ca_entries = [e for e in load_catalog() if e.get("scope") == "autonomous_communities"]
        operative = [e for e in ca_entries if e.get("access_mode") in {"operative", "open"}]
        manual = [e for e in ca_entries if e.get("access_mode") == "manual_download"]
        return ConnectorResult(
            status="skipped",
            message=(
                f"Comunidades autónomas: {len(ca_entries)} fuentes catalogadas "
                f"({len(operative)} operativas, {len(manual)} de descarga manual). "
                "Ingesta automática por portal pendiente de implementación verificada."
            ),
            source_metadata=ca_entries,
        )
