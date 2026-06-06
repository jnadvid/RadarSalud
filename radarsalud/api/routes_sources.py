"""Endpoints de fuentes."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from radarsalud.database import get_session
from radarsalud.models import Source
from radarsalud.schemas.source import SourceCreate, SourceRead, SourceToggle
from radarsalud.services import sources_service

router = APIRouter(prefix="/api/v1/sources", tags=["sources"])


@router.get("", response_model=list[SourceRead])
def list_sources(session: Session = Depends(get_session)) -> list[Source]:
    return list(session.scalars(select(Source).order_by(Source.name)).all())


@router.post("", response_model=SourceRead, status_code=201)
def create_source(payload: SourceCreate, session: Session = Depends(get_session)) -> Source:
    source = Source(**payload.model_dump())
    session.add(source)
    session.commit()
    session.refresh(source)
    return source


@router.post("/check")
def check_sources(
    include_datasets: bool = Query(default=False, description="Incluir datasets descubiertos"),
    session: Session = Depends(get_session),
):
    """Comprueba todas las fuentes con URL y marca las que no responden."""
    return sources_service.check_all_sources(session, include_datasets=include_datasets)


@router.patch("/{source_id}/toggle", response_model=SourceRead)
def toggle_source(
    source_id: int, payload: SourceToggle, session: Session = Depends(get_session)
) -> Source:
    """Activa o desactiva una fuente."""
    source = sources_service.set_enabled(session, source_id, payload.enabled)
    if source is None:
        raise HTTPException(status_code=404, detail="Fuente no encontrada")
    return source
