"""Conector BOE datos abiertos (avisos oficiales como señal contextual).

El BOE publica datos abiertos de disposiciones oficiales. Se usaría como señal
contextual (no como indicador epidemiológico directo). Plantilla documentada
hasta verificar el endpoint y el filtrado por materia sanitaria.

Doc oficial: https://www.boe.es/datosabiertos/
"""
from __future__ import annotations

from radarsalud.connectors.base import BaseConnector, ConnectorResult


class BoeConnector(BaseConnector):
    name = "boe_datos_abiertos"
    category = "boletin"
    source_type = "api"
    operational = False
    access_mode = "pending_verification"
    organization = "Boletín Oficial del Estado (BOE)"
    url = "https://www.boe.es/datosabiertos/"
    license = "BOE - datos abiertos"

    def fetch(self) -> ConnectorResult:
        return ConnectorResult(
            status="skipped",
            message=(
                "BOE datos abiertos: plantilla documentada. Uso como señal "
                "contextual de disposiciones sanitarias. Pendiente de fijar el "
                "endpoint y el filtrado por materia."
            ),
        )
