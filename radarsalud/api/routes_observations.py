"""Endpoints de observaciones."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from radarsalud.database import get_session
from radarsalud.models import Observation
from radarsalud.schemas.observation import ObservationCreate, ObservationRead

router = APIRouter(prefix="/api/v1/observations", tags=["observations"])


@router.get("", response_model=list[ObservationRead])
def list_observations(
    data_mode: str | None = Query(default=None, description="real|manual_import|simulation"),
    province: str | None = None,
    health_event: str | None = None,
    limit: int = Query(default=500, le=5000),
    session: Session = Depends(get_session),
) -> list[Observation]:
    stmt = select(Observation)
    if data_mode and data_mode != "all":
        stmt = stmt.where(Observation.data_mode == data_mode)
    if province:
        stmt = stmt.where(Observation.province == province)
    if health_event:
        stmt = stmt.where(Observation.health_event == health_event)
    stmt = stmt.order_by(Observation.observed_at.desc()).limit(limit)
    return list(session.scalars(stmt).all())


@router.post("", response_model=ObservationRead, status_code=201)
def create_observation(
    payload: ObservationCreate, session: Session = Depends(get_session)
) -> Observation:
    # Las observaciones creadas por API se etiquetan según data_mode del payload;
    # por defecto 'real'. La separación con simulación se preserva en el campo.
    obs = Observation(**payload.model_dump())
    session.add(obs)
    session.commit()
    session.refresh(obs)
    return obs
