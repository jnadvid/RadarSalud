"""Conector AEMET OpenData (temperatura, avisos, calor extremo).

Requiere API key gratuita (AEMET_API_KEY en .env). AEMET OpenData usa un patrón
de dos pasos: una primera llamada devuelve una URL temporal con los datos. Sin
clave, el conector queda desactivado pero documentado.

Doc oficial: https://opendata.aemet.es/
"""
from __future__ import annotations

from radarsalud.config import get_settings
from radarsalud.connectors.base import BaseConnector, ConnectorResult


class AemetConnector(BaseConnector):
    name = "aemet_opendata"
    category = "meteorologia"
    source_type = "api"
    requires_key = True
    access_mode = "api_key_required"
    organization = "Agencia Estatal de Meteorología (AEMET)"
    url = "https://opendata.aemet.es"
    license = "AEMET OpenData - condiciones de uso de AEMET"

    @property
    def operational(self) -> bool:  # type: ignore[override]
        return bool(get_settings().aemet_api_key)

    def is_available(self) -> bool:
        return self.operational

    def fetch(self) -> ConnectorResult:
        api_key = get_settings().aemet_api_key
        if not api_key:
            return ConnectorResult(
                status="skipped",
                message=(
                    "AEMET desactivado: falta AEMET_API_KEY en .env. Solicite una "
                    "clave gratuita en https://opendata.aemet.es/ para activar la "
                    "ingesta de temperatura y avisos meteorológicos."
                ),
            )
        # Plantilla: con clave disponible, aquí se implementaría el patrón de dos
        # pasos de AEMET OpenData para avisos CAP y temperatura por provincia. Se
        # deja documentado para no fijar endpoints sin verificación previa.
        return ConnectorResult(
            status="skipped",
            message=(
                "AEMET_API_KEY presente. Implementación de endpoints concretos "
                "(avisos CAP, climatología diaria) pendiente de verificación. "
                "Plantilla lista para completar sin OCR."
            ),
        )
