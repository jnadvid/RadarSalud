"""Modelo de alerta epidemiológica (real o simulada)."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from radarsalud.database import Base


class Alert(Base):
    """Señal de anomalía detectada sobre observaciones agregadas."""

    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # real, simulation (las alertas nunca son manual_import: se derivan del análisis)
    data_mode: Mapped[str] = mapped_column(String(20), default="real", index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    observed_at: Mapped[datetime | None] = mapped_column(DateTime, index=True)

    autonomous_community: Mapped[str | None] = mapped_column(String(100), index=True)
    province: Mapped[str | None] = mapped_column(String(100), index=True)
    municipality: Mapped[str | None] = mapped_column(String(150), nullable=True)
    province_code: Mapped[str | None] = mapped_column(String(5), nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)

    health_event: Mapped[str | None] = mapped_column(String(50), index=True)
    signal_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    # low, medium, high, critical
    severity: Mapped[str] = mapped_column(String(20), default="low", index=True)

    observed_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    baseline_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    deviation_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    recommendation: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_ids_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    # open, reviewed, dismissed
    status: Mapped[str] = mapped_column(String(20), default="open", index=True)

    simulation_id: Mapped[int | None] = mapped_column(
        ForeignKey("simulations.id"), nullable=True, index=True
    )

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<Alert {self.id} {self.data_mode} {self.severity} "
            f"{self.health_event} {self.province}>"
        )
