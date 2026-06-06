"""Conector INE (población por provincia/municipio para normalizar tasas).

El INE ofrece API JSON (Tempus3) y descargas CSV abiertas. El endpoint exacto
de la serie de población a usar debe fijarse y verificarse; en el MVP se deja
como plantilla documentada (manual_download) sin inventar URLs concretas.

Doc oficial: https://www.ine.es/dyngs/DataLab/manual.html
"""
from __future__ import annotations

from radarsalud.connectors.base import BaseConnector, ConnectorResult


class IneConnector(BaseConnector):
    name = "ine_poblacion"
    category = "poblacion"
    source_type = "api"
    operational = False
    access_mode = "manual_download"
    organization = "Instituto Nacional de Estadística (INE)"
    url = "https://www.ine.es"
    license = "INE - reutilización con cita de la fuente"

    def fetch(self) -> ConnectorResult:
        return ConnectorResult(
            status="skipped",
            message=(
                "INE: población por provincia/municipio para normalización de "
                "tasas. Plantilla documentada. Use la API Tempus3 o un CSV abierto "
                "del INE y cárguelo con `radarsalud import-csv` mientras se fija "
                "el endpoint estable."
            ),
        )
