"""Modelo de observación agregada (real, importada o simulada)."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from radarsalud.database import Base


class Observation(Base):
    """Señal agregada observada en un territorio y momento dados.

    Nunca contiene datos personales: solo agregados poblacionales.
    """

    __tablename__ = "observations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # real, manual_import, simulation
    data_mode: Mapped[str] = mapped_column(String(20), default="real", index=True)

    observed_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    ingested_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    autonomous_community: Mapped[str | None] = mapped_column(String(100), index=True)
    province: Mapped[str | None] = mapped_column(String(100), index=True)
    municipality: Mapped[str | None] = mapped_column(String(150), nullable=True)
    province_code: Mapped[str | None] = mapped_column(String(5), nullable=True)
    municipality_code: Mapped[str | None] = mapped_column(String(10), nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)

    signal_type: Mapped[str | None] = mapped_column(String(50), index=True)
    health_event: Mapped[str | None] = mapped_column(String(50), index=True)
    pathogen: Mapped[str | None] = mapped_column(String(80), nullable=True)
    value: Mapped[float | None] = mapped_column(Float, nullable=True)
    unit: Mapped[str | None] = mapped_column(String(50), nullable=True)

    source_id: Mapped[int | None] = mapped_column(ForeignKey("sources.id"), nullable=True)
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    raw_payload_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    normalized_payload_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Vínculo opcional a la simulación que la generó (si data_mode == simulation).
    simulation_id: Mapped[int | None] = mapped_column(
        ForeignKey("simulations.id"), nullable=True, index=True
    )

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<Observation {self.id} {self.data_mode} {self.health_event} "
            f"{self.province} {self.value}>"
        )
