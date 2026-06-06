"""Servicio de mapa: prepara alertas para el mapa Folium y el GeoJSON."""
from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

import json

from radarsalud.maps.folium_map import render_map_html
from radarsalud.maps.spain_geojson import SPAIN_CENTER
from radarsalud.models import Alert, Observation, Source
from radarsalud.normalizers.geography import centroid, community_centroid


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


def get_source_features(session: Session, *, only_enabled: bool = False) -> list[dict[str, Any]]:
    """Sitúa las fuentes en el mapa para enriquecerlo con su cobertura y estado.

    - Fuentes autonómicas -> centroide de su comunidad.
    - Fuentes nacionales  -> repartidas en una columna a la izquierda del mapa.
    Se omiten los datasets descubiertos (name 'dataset::...').
    El color refleja el estado de la última comprobación y si está habilitada.
    """
    stmt = select(Source).where(~Source.name.like("dataset::%"))
    if only_enabled:
        stmt = stmt.where(Source.enabled.is_(True))
    sources = session.scalars(stmt.order_by(Source.name)).all()

    features: list[dict[str, Any]] = []
    national_index = 0
    for s in sources:
        pos = community_centroid(s.autonomous_community) if s.autonomous_community else None
        level = "autonómica" if pos else "nacional"
        if pos is None:
            # Reparte las fuentes nacionales en una columna vertical a la izquierda.
            lat = 36.5 + (national_index % 12) * 0.55
            lon = SPAIN_CENTER[1] - 9.5
            pos = (lat, lon)
            national_index += 1

        if s.last_check_ok is True:
            status, color = "operativa", "#27ae60"
        elif s.last_check_ok is False:
            status, color = "caída", "#c0392b"
        else:
            status, color = "sin comprobar", "#95a5a6"

        features.append(
            {
                "name": s.name,
                "organization": s.organization,
                "level": level,
                "autonomous_community": s.autonomous_community,
                "category": s.category,
                "access_mode": s.access_mode,
                "enabled": bool(s.enabled),
                "status": status,
                "color": color,
                "http_status": s.last_check_http_status,
                "message": s.last_check_message,
                "last_checked_at": s.last_checked_at.isoformat() if s.last_checked_at else None,
                "url": s.url,
                "latitude": pos[0],
                "longitude": pos[1],
            }
        )
    return features


def get_observation_features(session: Session, mode: str = "all") -> list[dict[str, Any]]:
    """Último valor observado por territorio y señal, para mostrarlo en el mapa.

    Esto hace que el mapa muestre DATOS DE SALUD (no solo alertas): el valor más
    reciente por provincia/comunidad, con su baseline cuando la fuente lo aporta
    (p. ej. mortalidad esperada de MoMo) y un color según si hay exceso.
    """
    if mode == "real":
        modes = ["real", "manual_import"]
    elif mode == "simulation":
        modes = ["simulation"]
    else:
        modes = ["real", "manual_import", "simulation"]

    obs = session.scalars(
        select(Observation)
        .where(Observation.data_mode.in_(modes))
        .order_by(Observation.observed_at)
    ).all()

    # Última observación por (modo, territorio, señal, evento).
    latest: dict[tuple, Observation] = {}
    for o in obs:
        key = (o.data_mode, o.province or o.autonomous_community, o.signal_type, o.health_event)
        latest[key] = o  # orden ascendente: la última gana

    features: list[dict[str, Any]] = []
    for o in latest.values():
        lat, lon = o.latitude, o.longitude
        if lat is None or lon is None:
            c = centroid(o.province) or community_centroid(o.autonomous_community)
            if c:
                lat, lon = c
        if lat is None or lon is None:
            continue

        baseline = baseline_high = None
        if o.normalized_payload_json:
            try:
                p = json.loads(o.normalized_payload_json)
                baseline = p.get("esperadas_base")
                baseline_high = p.get("q99")
            except (ValueError, TypeError):
                pass

        if baseline_high is not None and o.value is not None and o.value > baseline_high:
            status, color = "exceso sobre lo esperado", "#e74c3c"
        elif baseline_high is not None and o.value is not None:
            status, color = "dentro de lo esperado", "#27ae60"
        else:
            status, color = "dato observado", "#2980b9"

        features.append(
            {
                "data_mode": o.data_mode,
                "is_sim": o.data_mode == "simulation",
                "health_event": o.health_event,
                "signal_type": o.signal_type,
                "province": o.province,
                "autonomous_community": o.autonomous_community,
                "observed_at": o.observed_at.isoformat() if o.observed_at else None,
                "value": o.value,
                "unit": o.unit,
                "baseline": baseline,
                "baseline_high": baseline_high,
                "status": status,
                "color": color,
                "latitude": lat,
                "longitude": lon,
            }
        )
    return features


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
    """HTML del mapa Folium: datos de salud + alertas + cobertura de fuentes."""
    return render_map_html(
        get_map_alerts(session, mode),
        sources=get_source_features(session),
        observations=get_observation_features(session, mode),
    )
