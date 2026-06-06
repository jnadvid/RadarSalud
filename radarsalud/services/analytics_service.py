"""Servicio de analítica: ejecuta la detección de anomalías y crea alertas.

Diferencia siempre por `data_mode`: nunca mezcla series reales y simuladas en
una misma detección. El modo 'all' analiza ambos por separado.
"""
from __future__ import annotations

import json
from datetime import datetime

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from radarsalud.analytics.anomalies import AnomalyResult, detect_anomalies
from radarsalud.models import Alert, Observation
from radarsalud.normalizers.geography import centroid, province_code
from radarsalud.utils.logging import get_logger

logger = get_logger(__name__)

# Equivalencia entre modo de análisis y modos de dato a incluir.
_MODE_GROUPS = {
    "real": ["real", "manual_import"],
    "simulation": ["simulation"],
}


def _load_dataframe(session: Session, data_modes: list[str], *, province=None,
                    health_event=None, signal_type=None, start=None, end=None) -> pd.DataFrame:
    stmt = select(Observation).where(Observation.data_mode.in_(data_modes))
    if province:
        stmt = stmt.where(Observation.province == province)
    if health_event:
        stmt = stmt.where(Observation.health_event == health_event)
    if signal_type:
        stmt = stmt.where(Observation.signal_type == signal_type)
    if start:
        stmt = stmt.where(Observation.observed_at >= start)
    if end:
        stmt = stmt.where(Observation.observed_at <= end)

    rows = session.scalars(stmt).all()
    records = [
        {
            "id": o.id,
            "observed_at": o.observed_at,
            "province": o.province,
            "autonomous_community": o.autonomous_community,
            "health_event": o.health_event,
            "signal_type": o.signal_type,
            "value": o.value,
            "source_id": o.source_id,
            "simulation_id": o.simulation_id,
            "latitude": o.latitude,
            "longitude": o.longitude,
        }
        for o in rows
    ]
    return pd.DataFrame.from_records(records)


def _alert_data_mode(analysis_mode_key: str) -> str:
    # Las alertas solo se etiquetan como 'real' o 'simulation'.
    return "simulation" if analysis_mode_key == "simulation" else "real"


def _persist_alerts(session: Session, results: list[AnomalyResult], *, alert_mode: str,
                    df: pd.DataFrame) -> int:
    created = 0
    for r in results:
        lat, lon = (None, None)
        c = centroid(r.province)
        if c:
            lat, lon = c

        simulation_id = None
        if alert_mode == "simulation" and not df.empty and "simulation_id" in df.columns:
            subset = df[
                (df["province"] == r.province)
                & (df["health_event"] == r.health_event)
                & (df["signal_type"] == r.signal_type)
            ]
            sim_ids = [int(s) for s in subset["simulation_id"].dropna().tolist()]
            if sim_ids:
                simulation_id = max(set(sim_ids), key=sim_ids.count)

        session.add(
            Alert(
                data_mode=alert_mode,
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


def run_analysis(session: Session, *, data_mode: str = "real", province=None,
                 health_event=None, signal_type=None, start=None, end=None,
                 replace_open: bool = True) -> dict:
    """Ejecuta la detección de anomalías y persiste alertas.

    data_mode: 'real' | 'simulation' | 'all'.
    """
    if data_mode == "all":
        mode_keys = ["real", "simulation"]
    elif data_mode in _MODE_GROUPS:
        mode_keys = [data_mode]
    else:
        raise ValueError(f"data_mode no válido: {data_mode}")

    summary = {"alerts_created": 0, "by_mode": {}}
    for key in mode_keys:
        alert_mode = _alert_data_mode(key)
        df = _load_dataframe(
            session, _MODE_GROUPS[key], province=province, health_event=health_event,
            signal_type=signal_type, start=start, end=end,
        )
        if replace_open:
            # Elimina alertas abiertas previas de ese modo para no duplicar.
            existing = session.scalars(
                select(Alert).where(Alert.data_mode == alert_mode, Alert.status == "open")
            ).all()
            for a in existing:
                session.delete(a)
            session.flush()

        results = detect_anomalies(df, data_mode=alert_mode)
        created = _persist_alerts(session, results, alert_mode=alert_mode, df=df)
        summary["alerts_created"] += created
        summary["by_mode"][key] = {"observations": int(len(df)), "alerts": created}

    session.commit()
    logger.info("Análisis (%s): %d alertas creadas", data_mode, summary["alerts_created"])
    return summary
