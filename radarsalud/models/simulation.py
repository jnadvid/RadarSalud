"""Modelo de simulación (lote de datos simulados separados de los reales)."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from radarsalud.database import Base


class Simulation(Base):
    """Registro de una ejecución de simulación de brote.

    Todas las observaciones y alertas que genera quedan marcadas con
    `data_mode = simulation` y vinculadas a este id, de modo que el lote
    completo puede limpiarse sin tocar los datos reales.
    """

    __tablename__ = "simulations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # created, running, completed, failed, cleared
    status: Mapped[str] = mapped_column(String(20), default="created", index=True)
    # gripe, covid, vrs, gastroenteritis, golpe_calor, multi_evento
    scenario_type: Mapped[str] = mapped_column(String(30), default="gripe")

    province: Mapped[str | None] = mapped_column(String(100), nullable=True)
    autonomous_community: Mapped[str | None] = mapped_column(String(100), nullable=True)
    severity: Mapped[str] = mapped_column(String(20), default="medium")
    days: Mapped[int] = mapped_column(Integer, default=14)
    multiplier: Mapped[float] = mapped_column(Float, default=2.0)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Simulation {self.id} {self.scenario_type} {self.status}>"
