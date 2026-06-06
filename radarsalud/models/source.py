"""Modelo de fuente de datos."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from radarsalud.database import Base


class Source(Base):
    """Catálogo de fuentes de datos (reales o plantilla pendiente)."""

    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    # api, csv, rss, html, manual
    source_type: Mapped[str] = mapped_column(String(20), default="api")
    # salud, meteorologia, aguas_residuales, calidad_aire, poblacion, boletin, rss, otro
    category: Mapped[str] = mapped_column(String(40), default="otro")
    url: Mapped[str | None] = mapped_column(Text, nullable=True)
    organization: Mapped[str | None] = mapped_column(String(200), nullable=True)
    license: Mapped[str | None] = mapped_column(String(200), nullable=True)
    # open, api_key_required, manual_download, pending_verification
    access_mode: Mapped[str] = mapped_column(String(30), default="pending_verification")
    refresh_frequency: Mapped[str | None] = mapped_column(String(50), nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_real_source: Mapped[bool] = mapped_column(Boolean, default=True)

    def __repr__(self) -> str:  # pragma: no cover - representación de depuración
        return f"<Source {self.id} {self.name!r} {self.access_mode}>"
