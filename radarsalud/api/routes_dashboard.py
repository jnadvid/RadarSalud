"""Endpoints del panel: resúmenes, gráficas en tiempo real y pipeline."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from radarsalud.database import get_session
from radarsalud.services import (
    dashboard_service,
    export_service,
    pipeline_service,
    scheduler_service,
)

router = APIRouter(prefix="/api/v1", tags=["dashboard"])


@router.get("/dashboard/summary")
def summary(session: Session = Depends(get_session)):
    return dashboard_service.summary(session)


@router.get("/dashboard/mortality_timeseries")
def mortality_timeseries(session: Session = Depends(get_session)):
    return dashboard_service.mortality_timeseries(session)


@router.get("/dashboard/top_excess")
def top_excess(limit: int = 10, session: Session = Depends(get_session)):
    return dashboard_service.top_excess(session, limit=limit)


class RefreshRequest(BaseModel):
    include_heavy: bool = True  # incluir mortalidad MoMo (descarga grande)
    include_light: bool = True


@router.post("/pipeline/refresh")
def pipeline_refresh(payload: RefreshRequest | None = None):
    """Lanza en segundo plano: ingesta de datos reales + análisis."""
    payload = payload or RefreshRequest()
    started = pipeline_service.start_refresh(
        include_light=payload.include_light, include_heavy=payload.include_heavy
    )
    return {"started": started, "state": pipeline_service.get_state()}


@router.get("/pipeline/status")
def pipeline_status():
    return pipeline_service.get_state()


@router.get("/dashboard/province_timeseries")
def province_timeseries(province: str, session: Session = Depends(get_session)):
    return dashboard_service.province_timeseries(session, province)


# --- Scheduler (actualización automática) -----------------------------------
class SchedulerRequest(BaseModel):
    hours: float = 12.0
    include_heavy: bool = True


@router.get("/scheduler/status")
def scheduler_status():
    return scheduler_service.status()


@router.post("/scheduler/start")
def scheduler_start(payload: SchedulerRequest | None = None):
    payload = payload or SchedulerRequest()
    return scheduler_service.start(hours=payload.hours, include_heavy=payload.include_heavy)


@router.post("/scheduler/stop")
def scheduler_stop():
    return scheduler_service.stop()


# --- Exportación de datos ----------------------------------------------------
@router.get("/observations.csv", response_class=PlainTextResponse)
def export_observations(
    data_mode: str | None = Query(default=None),
    province: str | None = None,
    health_event: str | None = None,
    session: Session = Depends(get_session),
):
    csv_text = export_service.observations_csv(
        session, data_mode=data_mode, province=province, health_event=health_event
    )
    return PlainTextResponse(
        csv_text,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=observaciones.csv"},
    )


@router.get("/alerts.csv", response_class=PlainTextResponse)
def export_alerts(
    data_mode: str | None = Query(default=None),
    session: Session = Depends(get_session),
):
    csv_text = export_service.alerts_csv(session, data_mode=data_mode)
    return PlainTextResponse(
        csv_text,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=alertas.csv"},
    )
