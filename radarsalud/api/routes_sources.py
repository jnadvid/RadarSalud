"""Endpoints de fuentes."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from radarsalud.database import get_session
from radarsalud.models import Source
from radarsalud.schemas.source import SourceCreate, SourceRead

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
