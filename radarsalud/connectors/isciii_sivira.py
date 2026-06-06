"""Conector ISCIII / SiVIRA (vigilancia de infecciones respiratorias agudas).

SiVIRA integra la vigilancia de gripe, COVID-19 y VRS. Buena parte de la
información se difunde en informes (PDF/web no estructurada). En el MVP no se usa
OCR ni scraping agresivo: se deja como plantilla documentada hasta confirmar un
recurso estructurado abierto y estable.

Doc oficial: https://www.isciii.es
"""
from __future__ import annotations

from radarsalud.connectors.base import BaseConnector, ConnectorResult


class IsciiiSiviraConnector(BaseConnector):
    name = "isciii_sivira"
    category = "salud"
    source_type = "html"
    operational = False
    access_mode = "pending_verification"
    organization = "Instituto de Salud Carlos III (ISCIII) - SiVIRA"
    url = "https://www.isciii.es"
    license = "ISCIII - condiciones institucionales"

    def fetch(self) -> ConnectorResult:
        return ConnectorResult(
            status="skipped",
            message=(
                "ISCIII/SiVIRA: vigilancia de gripe, COVID-19 y VRS. Plantilla "
                "documentada. Pendiente de confirmar un recurso estructurado "
                "abierto (CSV/JSON). No se usa OCR en el MVP. Mientras tanto, los "
                "datos agregados pueden cargarse vía `radarsalud import-csv`."
            ),
        )
