"""Conectores de fuentes abiertas reales.

Cada conector declara su nombre, si está operativo y un método `fetch()` que
devuelve observaciones normalizadas. Los conectores que requieren clave o
descarga manual quedan documentados y desactivados (operational=False).
"""
from __future__ import annotations

from radarsalud.connectors.base import BaseConnector, ConnectorResult
from radarsalud.connectors.calidad_aire import CalidadAireConnector
from radarsalud.connectors.datos_gob import DatosGobConnector
from radarsalud.connectors.aemet import AemetConnector
from radarsalud.connectors.aguas_residuales import AguasResidualesConnector
from radarsalud.connectors.boe import BoeConnector
from radarsalud.connectors.comunidades_autonomas import ComunidadesAutonomasConnector
from radarsalud.connectors.csv_local import CsvLocalConnector
from radarsalud.connectors.ine import IneConnector
from radarsalud.connectors.isciii_sivira import IsciiiSiviraConnector
from radarsalud.connectors.ministerio_sanidad import MinisterioSanidadConnector
from radarsalud.connectors.rss_institucional import RssInstitucionalConnector


def get_connectors() -> list[BaseConnector]:
    """Instancia todos los conectores conocidos."""
    return [
        DatosGobConnector(),
        RssInstitucionalConnector(),
        IneConnector(),
        AemetConnector(),
        IsciiiSiviraConnector(),
        MinisterioSanidadConnector(),
        CalidadAireConnector(),
        AguasResidualesConnector(),
        BoeConnector(),
        ComunidadesAutonomasConnector(),
        CsvLocalConnector(),
    ]


def get_connector(name: str) -> BaseConnector | None:
    for c in get_connectors():
        if c.name == name:
            return c
    return None


__all__ = [
    "BaseConnector",
    "ConnectorResult",
    "get_connectors",
    "get_connector",
]
