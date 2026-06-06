"""Servicio de mapa: prepara alertas para el mapa Folium y el GeoJSON."""
from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from radarsalud.maps.folium_map import render_map_html
from radarsalud.models import Alert, Source
from radarsalud.normalizers.geography import centroid


def _mode_filter(mode: str) -> list[str]:
    if mode == "real":
        return ["real"]
    if mode == "simulation":
        return ["simulation"]
    return ["real", "simulation"]  # all


def get_map_alerts(session: Session, mode: str = "all") -> list[dict[str, Any]]:
    """Devuelve alertas listas para pintar, resolviendo coordenadas y fuente."""
    modes = _mode_filter(mode)
    alerts = session.scalars(select(Alert).where(Alert.data_mode.in_(modes))).all()

    # Cache de nombres de fuente.
    source_names = {s.id: s.name for s in session.scalars(select(Source)).all()}

    items: list[dict[str, Any]] = []
    for a in alerts:
        lat, lon = a.latitude, a.longitude
        if lat is None or lon is None:
            c = centroid(a.province)
            if c:
                lat, lon = c
        if lat is None or lon is None:
            continue

        source_label = None
        if a.source_ids_json:
            try:
                import json

                ids = json.loads(a.source_ids_json)
                names = [source_names.get(i) for i in ids if source_names.get(i)]
                source_label = ", ".join(names) if names else None
            except Exception:  # noqa: BLE001
                source_label = None

        items.append(
            {
                "data_mode": a.data_mode,
                "health_event": a.health_event,
                "province": a.province,
                "autonomous_community": a.autonomous_community,
                "observed_at": a.observed_at.isoformat() if a.observed_at else None,
                "severity": a.severity,
                "observed_value": a.observed_value,
                "baseline_value": a.baseline_value,
                "explanation": a.explanation,
                "recommendation": a.recommendation,
                "source": source_label or "—",
                "latitude": lat,
                "longitude": lon,
            }
        )
    return items


def build_geojson(session: Session, mode: str = "all") -> dict[str, Any]:
    """FeatureCollection GeoJSON de las alertas según el modo."""
    features = []
    for a in get_map_alerts(session, mode):
        features.append(
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [a["longitude"], a["latitude"]],
                },
                "properties": {k: v for k, v in a.items() if k not in {"latitude", "longitude"}},
            }
        )
    return {"type": "FeatureCollection", "features": features}


def render_map(session: Session, mode: str = "all") -> str:
    """HTML del mapa Folium para el modo indicado."""
    return render_map_html(get_map_alerts(session, mode))
