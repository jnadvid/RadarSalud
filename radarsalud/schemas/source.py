"""Esquemas de fuente."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

__all__ = ["SourceBase", "SourceCreate", "SourceRead", "SourceToggle"]


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
    autonomous_community: str | None = None
    last_checked_at: datetime | None = None
    last_check_ok: bool | None = None
    last_check_http_status: int | None = None
    last_check_message: str | None = None


class SourceToggle(BaseModel):
    enabled: bool
