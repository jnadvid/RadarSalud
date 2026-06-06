"""Esquemas de fuente."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SourceBase(BaseModel):
    name: str
    source_type: str = "api"
    category: str = "otro"
    url: str | None = None
    organization: str | None = None
    license: str | None = None
    access_mode: str = "pending_verification"
    refresh_frequency: str | None = None
    enabled: bool = False
    notes: str | None = None
    is_real_source: bool = True


class SourceCreate(SourceBase):
    pass


class SourceRead(SourceBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    last_checked_at: datetime | None = None
