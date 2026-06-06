"""Endpoints de analítica (ejecución de detección de anomalías)."""
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from radarsalud.database import get_session
from radarsalud.services import analytics_service

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])


class AnalyticsRequest(BaseModel):
    data_mode: str = "real"  # real | simulation | all
    province: str | None = None
    health_event: str | None = None
    signal_type: str | None = None
    start: datetime | None = None
    end: datetime | None = None


@router.post("/run")
def run_analytics(payload: AnalyticsRequest, session: Session = Depends(get_session)):
    try:
        return analytics_service.run_analysis(
            session,
            data_mode=payload.data_mode,
            province=payload.province,
            health_event=payload.health_event,
            signal_type=payload.signal_type,
            start=payload.start,
            end=payload.end,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
