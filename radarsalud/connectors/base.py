"""Clase base de los conectores de fuentes abiertas."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ConnectorResult:
    """Resultado de una ejecución de conector.

    - observations: lista de dicts listos para insertar como Observation real.
    - source_metadata: metadatos de datasets/fuentes descubiertos (datos.gob...).
    - status: success | skipped | failed | partial
    - message: texto informativo (motivo de skip, error, etc.).
    """

    observations: list[dict[str, Any]] = field(default_factory=list)
    source_metadata: list[dict[str, Any]] = field(default_factory=list)
    status: str = "success"
    message: str = ""

    @property
    def records_found(self) -> int:
        return len(self.observations)


class BaseConnector:
    """Interfaz común de los conectores.

    Atributos de clase a sobrescribir:
      name           identificador único (coincide con `sources.name`).
      category       categoría de la fuente.
      operational    True si puede ejecutarse en el MVP sin claves ni descarga manual.
      requires_key   True si necesita una API key (se desactiva si falta).
      access_mode    estado declarado para el catálogo.
    """

    name: str = "base"
    category: str = "otro"
    source_type: str = "api"
    operational: bool = False
    requires_key: bool = False
    # heavy=True: descarga/proceso costoso; se excluye de `ingest-all` por defecto.
    heavy: bool = False
    access_mode: str = "pending_verification"
    organization: str | None = None
    url: str | None = None
    license: str | None = None

    def is_available(self) -> bool:
        """Indica si el conector puede ejecutar una ingesta real ahora mismo."""
        return self.operational

    def fetch(self) -> ConnectorResult:
        """Recupera y normaliza datos. Por defecto, plantilla no operativa."""
        return ConnectorResult(
            status="skipped",
            message=(
                f"Conector '{self.name}' no operativo en el MVP. "
                "Plantilla documentada pendiente de verificación o configuración."
            ),
        )
