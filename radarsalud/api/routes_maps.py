"""Endpoints de mapa (GeoJSON de alertas)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from radarsalud.database import get_session
from radarsalud.services import map_service

router = APIRouter(prefix="/api/v1/maps", tags=["maps"])


@router.get("/alerts.geojson")
def alerts_geojson(
    mode: str = Query(default="all", pattern="^(real|simulation|all)$"),
    session: Session = Depends(get_session),
):
    """FeatureCollection GeoJSON de alertas. mode = real | simulation | all."""
    return map_service.build_geojson(session, mode)
