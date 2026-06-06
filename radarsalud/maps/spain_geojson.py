"""GeoJSON de referencia de España basado en centroides de provincia.

El MVP usa marcadores por provincia (puntos en el centroide) en lugar de
polígonos pesados, para mantener el repositorio ligero y sin dependencias de
ficheros geográficos grandes. La capa de polígonos queda como trabajo futuro.
"""
from __future__ import annotations

from typing import Any

from radarsalud.normalizers.geography import PROVINCES

# Centro y zoom razonables para encuadrar la España peninsular + islas.
SPAIN_CENTER: tuple[float, float] = (40.0, -3.7)
SPAIN_ZOOM: int = 6


def provinces_point_geojson() -> dict[str, Any]:
    """FeatureCollection con un punto por provincia (centroide)."""
    features = []
    for p in PROVINCES:
        features.append(
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [p.longitude, p.latitude]},
                "properties": {
                    "name": p.name,
                    "code": p.code,
                    "autonomous_community": p.autonomous_community,
                },
            }
        )
    return {"type": "FeatureCollection", "features": features}
