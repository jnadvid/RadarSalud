"""Esquemas de alerta."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AlertRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    data_mode: str
    created_at: datetime | None = None
    observed_at: datetime | None = None
    autonomous_community: str | None = None
    province: str | None = None
    municipality: str | None = None
    province_code: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    health_event: str | None = None
    signal_type: str | None = None
    severity: str
    observed_value: float | None = None
    baseline_value: float | None = None
    deviation_score: float | None = None
    explanation: str | None = None
    recommendation: str | None = None
    status: str
    simulation_id: int | None = None


class AlertStatusUpdate(BaseModel):
    status: str  # open | reviewed | dismissed
