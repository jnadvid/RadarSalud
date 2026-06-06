"""Exportación de datos a CSV para analistas e investigación.

Solo exporta datos agregados (sin datos personales), respetando el `data_mode`.
"""
from __future__ import annotations

import csv
import io

from sqlalchemy import select
from sqlalchemy.orm import Session

from radarsalud.models import Alert, Observation

_OBS_FIELDS = [
    "id", "data_mode", "observed_at", "autonomous_community", "province",
    "province_code", "municipality", "signal_type", "health_event", "pathogen",
    "value", "unit", "confidence_score", "source_id", "simulation_id",
]
_ALERT_FIELDS = [
    "id", "data_mode", "created_at", "observed_at", "autonomous_community",
    "province", "health_event", "signal_type", "severity", "observed_value",
    "baseline_value", "deviation_score", "status", "explanation", "recommendation",
]


def observations_csv(session: Session, *, data_mode: str | None = None,
                     province: str | None = None, health_event: str | None = None,
                     limit: int = 100000) -> str:
    stmt = select(Observation)
    if data_mode and data_mode != "all":
        if data_mode == "real":
            stmt = stmt.where(Observation.data_mode.in_(["real", "manual_import"]))
        else:
            stmt = stmt.where(Observation.data_mode == data_mode)
    if province:
        stmt = stmt.where(Observation.province == province)
    if health_event:
        stmt = stmt.where(Observation.health_event == health_event)
    stmt = stmt.order_by(Observation.observed_at.desc()).limit(limit)

    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=_OBS_FIELDS, extrasaction="ignore")
    writer.writeheader()
    for o in session.scalars(stmt).all():
        row = {f: getattr(o, f) for f in _OBS_FIELDS}
        row["observed_at"] = o.observed_at.isoformat() if o.observed_at else ""
        writer.writerow(row)
    return buf.getvalue()


def alerts_csv(session: Session, *, data_mode: str | None = None,
               limit: int = 100000) -> str:
    stmt = select(Alert)
    if data_mode and data_mode != "all":
        stmt = stmt.where(Alert.data_mode == data_mode)
    stmt = stmt.order_by(Alert.created_at.desc()).limit(limit)

    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=_ALERT_FIELDS, extrasaction="ignore")
    writer.writeheader()
    for a in session.scalars(stmt).all():
        row = {f: getattr(a, f) for f in _ALERT_FIELDS}
        row["created_at"] = a.created_at.isoformat() if a.created_at else ""
        row["observed_at"] = a.observed_at.isoformat() if a.observed_at else ""
        writer.writerow(row)
    return buf.getvalue()
