"""Servicio de simulación: ejecuta escenarios y limpia simulaciones.

Garantiza la SEPARACIÓN total respecto a los datos reales: todo lo que genera
lleva `data_mode = simulation` y queda vinculado a un `simulation_id`, de modo
que puede borrarse por completo sin tocar ni una fila real.
"""
from __future__ import annotations

import json
from datetime import datetime

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from radarsalud.analytics.anomalies import detect_anomalies
from radarsalud.models import Alert, Observation, Simulation
from radarsalud.normalizers.geography import province_code
from radarsalud.simulation.engine import generate_observations
from radarsalud.simulation.presets import Preset, get_preset
from radarsalud.utils.logging import get_logger

logger = get_logger(__name__)


def run_simulation(session: Session, *, event: str, province: str | None = None,
                   autonomous_community: str | None = None, severity: str = "medium",
                   days: int = 14, multiplier: float = 2.0, name: str | None = None,
                   description: str | None = None, seed: int | None = None) -> dict:
    """Crea una simulación, genera observaciones y alertas simuladas."""
    scenario_type = event if event in {
        "gripe", "covid", "vrs", "gastroenteritis", "golpe_calor", "multi_evento"
    } else "gripe"

    sim = Simulation(
        name=name or f"Simulación {scenario_type} {datetime.utcnow():%Y-%m-%d %H:%M}",
        description=description,
        status="running",
        scenario_type=scenario_type,
        province=province,
        autonomous_community=autonomous_community,
        severity=severity,
        days=days,
        multiplier=multiplier,
        started_at=datetime.utcnow(),
        notes="Datos simulados. No representan una situación sanitaria real.",
    )
    session.add(sim)
    session.flush()  # obtener sim.id

    try:
        obs_dicts = generate_observations(
            event=event, province=province, autonomous_community=autonomous_community,
            severity=severity, days=days, multiplier=multiplier, seed=seed,
        )
        for od in obs_dicts:
            session.add(
                Observation(
                    data_mode="simulation",
                    simulation_id=sim.id,
                    observed_at=od["observed_at"],
                    autonomous_community=od.get("autonomous_community"),
                    province=od.get("province"),
                    municipality=od.get("municipality"),
                    province_code=province_code(od.get("province")),
                    latitude=od.get("latitude"),
                    longitude=od.get("longitude"),
                    signal_type=od.get("signal_type"),
                    health_event=od.get("health_event"),
                    pathogen=od.get("pathogen"),
                    value=od.get("value"),
                    unit=od.get("unit"),
                    confidence_score=od.get("confidence_score"),
                )
            )
        session.flush()

        alerts_created = _generate_simulation_alerts(session, sim.id)

        sim.status = "completed"
        sim.finished_at = datetime.utcnow()
        session.commit()
    except Exception:
        sim.status = "failed"
        sim.finished_at = datetime.utcnow()
        session.commit()
        raise

    return {
        "simulation_id": sim.id,
        "observations_created": len(obs_dicts),
        "alerts_created": alerts_created,
    }


def _generate_simulation_alerts(session: Session, simulation_id: int) -> int:
    """Detecta anomalías sobre las observaciones de UNA simulación y crea alertas."""
    import pandas as pd

    rows = session.scalars(
        select(Observation).where(Observation.simulation_id == simulation_id)
    ).all()
    df = pd.DataFrame.from_records(
        [
            {
                "observed_at": o.observed_at,
                "province": o.province,
                "autonomous_community": o.autonomous_community,
                "health_event": o.health_event,
                "signal_type": o.signal_type,
                "value": o.value,
                "source_id": o.source_id,
                "latitude": o.latitude,
                "longitude": o.longitude,
            }
            for o in rows
        ]
    )
    results = detect_anomalies(df, data_mode="simulation")
    created = 0
    for r in results:
        # Coordenadas: usa el centroide provincial guardado en las observaciones.
        lat = lon = None
        if not df.empty:
            subset = df[(df["province"] == r.province) & (df["health_event"] == r.health_event)]
            if not subset.empty:
                lat = subset.iloc[-1].get("latitude")
                lon = subset.iloc[-1].get("longitude")
        session.add(
            Alert(
                data_mode="simulation",
                observed_at=r.observed_at if isinstance(r.observed_at, datetime) else None,
                autonomous_community=r.autonomous_community,
                province=r.province,
                province_code=province_code(r.province),
                latitude=lat,
                longitude=lon,
                health_event=r.health_event,
                signal_type=r.signal_type,
                severity=r.severity,
                observed_value=r.observed_value,
                baseline_value=r.baseline_value,
                deviation_score=r.deviation_score,
                explanation=r.explanation,
                recommendation=r.recommendation,
                source_ids_json=json.dumps(r.source_ids),
                status="open",
                simulation_id=simulation_id,
            )
        )
        created += 1
    return created


def run_preset(session: Session, preset_name: str, seed: int | None = None) -> dict:
    preset: Preset | None = get_preset(preset_name)
    if preset is None:
        raise ValueError(f"Preset desconocido: {preset_name}")
    return run_simulation(
        session,
        event=preset.event,
        province=preset.province,
        autonomous_community=preset.autonomous_community,
        severity=preset.severity,
        days=preset.days,
        multiplier=preset.multiplier,
        name=preset.label,
        description=preset.description,
        seed=seed,
    )


def clear_simulations(session: Session) -> dict:
    """Elimina TODAS las observaciones y alertas simuladas. No toca datos reales."""
    obs_count = session.scalar(
        select(func.count()).select_from(Observation).where(
            Observation.data_mode == "simulation"
        )
    ) or 0
    alert_count = session.scalar(
        select(func.count()).select_from(Alert).where(Alert.data_mode == "simulation")
    ) or 0

    session.execute(delete(Observation).where(Observation.data_mode == "simulation"))
    session.execute(delete(Alert).where(Alert.data_mode == "simulation"))

    sims = session.scalars(select(Simulation)).all()
    cleared = 0
    for sim in sims:
        if sim.status != "cleared":
            sim.status = "cleared"
            sim.finished_at = sim.finished_at or datetime.utcnow()
            cleared += 1
    session.commit()
    logger.info("Simulaciones limpiadas: %d sims, %d obs, %d alertas",
                cleared, obs_count, alert_count)
    return {
        "simulations_cleared": cleared,
        "observations_deleted": int(obs_count),
        "alerts_deleted": int(alert_count),
    }


def list_simulations(session: Session) -> list[Simulation]:
    return list(session.scalars(select(Simulation).order_by(Simulation.created_at.desc())).all())
