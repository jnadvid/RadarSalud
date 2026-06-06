"""Conector Ministerio de Sanidad (boletines y datos de salud pública).

Plantilla documentada: pendiente de localizar descargas estructuradas abiertas
y estables. No se realiza scraping agresivo.

Doc oficial: https://www.sanidad.gob.es
"""
from __future__ import annotations

from radarsalud.connectors.base import BaseConnector, ConnectorResult


class MinisterioSanidadConnector(BaseConnector):
    name = "ministerio_sanidad"
    category = "salud"
    source_type = "html"
    operational = False
    access_mode = "pending_verification"
    organization = "Ministerio de Sanidad"
    url = "https://www.sanidad.gob.es"
    license = "Ministerio de Sanidad - condiciones institucionales"

    def fetch(self) -> ConnectorResult:
        return ConnectorResult(
            status="skipped",
            message=(
                "Ministerio de Sanidad: plantilla documentada. Pendiente de "
                "localizar recursos abiertos estructurados estables. Considere "
                "datasets publicados en datos.gob.es (ya cubiertos por su conector)."
            ),
        )
