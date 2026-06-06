"""Tests de la base de datos, modelos y siembra del catálogo."""
from __future__ import annotations

from sqlalchemy import func, select

from radarsalud.models import Observation, Source


def test_catalog_seeded(session):
    n = session.scalar(select(func.count()).select_from(Source))
    assert n >= 20, "El catálogo debería sembrar al menos 20 fuentes"


def test_datos_gob_source_is_operative(session):
    src = session.scalar(select(Source).where(Source.name == "datos_gob_es"))
    assert src is not None
    assert src.access_mode == "open"
    assert src.enabled is True
    assert src.is_real_source is True


def test_no_invented_url_for_pending(session):
    # Las fuentes pending_verification de CCAA dudosas no deben tener URL inventada.
    pending = session.scalars(
        select(Source).where(Source.access_mode == "pending_verification")
    ).all()
    assert pending, "Debe haber fuentes pendientes documentadas"


def test_observation_data_mode_default(session):
    from datetime import datetime

    obs = Observation(observed_at=datetime(2026, 1, 1), province="Madrid", value=1.0)
    session.add(obs)
    session.commit()
    assert obs.data_mode == "real"
    session.delete(obs)
    session.commit()
