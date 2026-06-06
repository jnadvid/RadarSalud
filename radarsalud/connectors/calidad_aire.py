"""Conector de calidad del aire (índices por estación/provincia).

Las series abiertas se reparten entre el MITECO y las CCAA, con formatos
heterogéneos. Plantilla documentada hasta fijar un endpoint abierto estable que
permita normalizar por provincia/municipio.
"""
from __future__ import annotations

from radarsalud.connectors.base import BaseConnector, ConnectorResult


class CalidadAireConnector(BaseConnector):
    name = "calidad_aire_nacional"
    category = "calidad_aire"
    source_type = "api"
    operational = False
    access_mode = "pending_verification"
    organization = "MITECO / Comunidades Autónomas"
    url = None
    license = "Variable por administración"

    def fetch(self) -> ConnectorResult:
        return ConnectorResult(
            status="skipped",
            message=(
                "Calidad del aire: plantilla documentada. Pendiente de fijar un "
                "endpoint abierto estable (estaciones del MITECO o portales "
                "autonómicos) y su mapeo a provincia/municipio."
            ),
        )
