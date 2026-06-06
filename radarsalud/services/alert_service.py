"""Servicio de alertas: consulta y actualización de estado."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from radarsalud.models import Alert

VALID_STATUSES = {"open", "reviewed", "dismissed"}


def list_alerts(session: Session, *, data_mode: str | None = None, province: str | None = None,
                health_event: str | None = None, severity: str | None = None,
                status: str | None = None, limit: int = 500) -> list[Alert]:
    stmt = select(Alert)
    if data_mode and data_mode != "all":
        stmt = stmt.where(Alert.data_mode == data_mode)
    if province:
        stmt = stmt.where(Alert.province == province)
    if health_event:
        stmt = stmt.where(Alert.health_event == health_event)
    if severity:
        stmt = stmt.where(Alert.severity == severity)
    if status:
        stmt = stmt.where(Alert.status == status)
    stmt = stmt.order_by(Alert.created_at.desc()).limit(limit)
    return list(session.scalars(stmt).all())


def update_status(session: Session, alert_id: int, status: str) -> Alert | None:
    if status not in VALID_STATUSES:
        raise ValueError(f"Estado no válido: {status}")
    alert = session.get(Alert, alert_id)
    if alert is None:
        return None
    alert.status = status
    session.commit()
    return alert
