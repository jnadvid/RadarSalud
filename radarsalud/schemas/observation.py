"""Esquemas de observación."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ObservationBase(BaseModel):
    data_mode: str = Field(default="real", description="real | manual_import | simulation")
    observed_at: datetime
    autonomous_community: str | None = None
    province: str | None = None
    municipality: str | None = None
    province_code: str | None = None
    municipality_code: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    signal_type: str | None = None
    health_event: str | None = None
    pathogen: str | None = None
    value: float | None = None
    unit: str | None = None
    source_id: int | None = None
    confidence_score: float | None = None


class ObservationCreate(ObservationBase):
    pass


class ObservationRead(ObservationBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ingested_at: datetime | None = None
    simulation_id: int | None = None
