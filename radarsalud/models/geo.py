"""Modelo de unidad geográfica (provincia / comunidad autónoma) para España."""
from __future__ import annotations

from sqlalchemy import Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from radarsalud.database import Base


class GeoUnit(Base):
    """Unidad territorial de referencia con centroide para el mapa.

    Se siembra con las 50 provincias + Ceuta y Melilla y sus centroides
    aproximados, usados para situar marcadores cuando una observación no
    trae coordenadas propias.
    """

    __tablename__ = "geo_units"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # provincia | comunidad_autonoma
    level: Mapped[str] = mapped_column(String(30), default="provincia", index=True)
    name: Mapped[str] = mapped_column(String(100), index=True)
    code: Mapped[str | None] = mapped_column(String(5), nullable=True, index=True)
    autonomous_community: Mapped[str | None] = mapped_column(String(100), nullable=True)
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<GeoUnit {self.level} {self.name!r} {self.code}>"
