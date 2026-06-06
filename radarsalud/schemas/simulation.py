"""Esquemas de simulación."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SimulationRequest(BaseModel):
    """Parámetros para lanzar una simulación a medida."""

    event: str = Field(default="gripe", description="gripe|covid|vrs|gastroenteritis|golpe_calor|multi_evento")
    province: str | None = None
    autonomous_community: str | None = None
    severity: str = "medium"
    days: int = Field(default=14, ge=1, le=120)
    multiplier: float = Field(default=2.0, gt=0, le=20)
    name: str | None = None
    description: str | None = None


class SimulationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None = None
    created_at: datetime | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    status: str
    scenario_type: str
    province: str | None = None
    autonomous_community: str | None = None
    severity: str
    days: int
    multiplier: float
    notes: str | None = None


class SimulationResult(BaseModel):
    simulation: SimulationRead
    observations_created: int
    alerts_created: int


class ClearResult(BaseModel):
    simulations_cleared: int
    observations_deleted: int
    alerts_deleted: int
