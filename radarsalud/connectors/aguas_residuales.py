"""Conector de vigilancia en aguas residuales (carga viral como señal temprana).

La disponibilidad y el formato abierto de estos programas (p. ej. SARS-CoV-2 en
aguas) varían por CCAA. Plantilla documentada hasta verificar una fuente abierta
estable. Si dispone de un CSV agregado, cárguelo con `radarsalud import-csv`.
"""
from __future__ import annotations

from radarsalud.connectors.base import BaseConnector, ConnectorResult


class AguasResidualesConnector(BaseConnector):
    name = "aguas_residuales"
    category = "aguas_residuales"
    source_type = "csv"
    operational = False
    access_mode = "pending_verification"
    organization = "Programas de vigilancia en aguas residuales"
    url = None
    license = "Variable por programa/CCAA"

    def fetch(self) -> ConnectorResult:
        return ConnectorResult(
            status="skipped",
            message=(
                "Aguas residuales: plantilla documentada. Señal temprana muy útil, "
                "pero disponibilidad/formato abiertos variables. Pendiente de "
                "verificación de fuente estable."
            ),
        )
