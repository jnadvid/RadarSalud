"""Endpoints de alertas."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from radarsalud.database import get_session
from radarsalud.schemas.alert import AlertRead, AlertStatusUpdate
from radarsalud.services import alert_service

router = APIRouter(prefix="/api/v1/alerts", tags=["alerts"])


@router.get("", response_model=list[AlertRead])
def list_alerts(
    data_mode: str | None = Query(default=None, description="real|simulation|all"),
    province: str | None = None,
    health_event: str | None = None,
    severity: str | None = None,
    status: str | None = None,
    limit: int = Query(default=500, le=5000),
    session: Session = Depends(get_session),
):
    return alert_service.list_alerts(
        session, data_mode=data_mode, province=province, health_event=health_event,
        severity=severity, status=status, limit=limit,
    )


@router.patch("/{alert_id}/status", response_model=AlertRead)
def update_alert_status(
    alert_id: int, payload: AlertStatusUpdate, session: Session = Depends(get_session)
):
    try:
        alert = alert_service.update_status(session, alert_id, payload.status)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if alert is None:
        raise HTTPException(status_code=404, detail="Alerta no encontrada")
    return alert
