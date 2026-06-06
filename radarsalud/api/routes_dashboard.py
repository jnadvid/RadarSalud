"""Endpoints del panel: resúmenes, gráficas en tiempo real y pipeline."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from radarsalud.database import get_session
from radarsalud.services import dashboard_service, pipeline_service

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
