"""Tests de gestión de fuentes: comprobación, toggle y enriquecimiento del mapa."""
from __future__ import annotations

import httpx
from sqlalchemy import select

from radarsalud.models import Source
from radarsalud.services import map_service, sources_service


def test_check_source_without_url_marks_not_checkable(session):
    src = session.scalar(
        select(Source).where(Source.url.is_(None)).limit(1)
    )
    assert src is not None
    result = sources_service.check_source(session, src)
    session.commit()
    assert result["ok"] is None
    assert "Sin URL" in (src.last_check_message or "")
    assert src.last_checked_at is not None


def test_check_source_handles_network_error(session, monkeypatch):
    src = session.scalar(select(Source).where(Source.url.isnot(None)).limit(1))
    assert src is not None

    def boom(*args, **kwargs):
        raise httpx.ConnectError("sin red")

    monkeypatch.setattr(sources_service, "polite_get", boom)
    result = sources_service.check_source(session, src)
    session.commit()
    assert result["ok"] is False
    assert "Error de red" in src.last_check_message


def test_set_enabled_toggle(session):
    src = session.scalars(select(Source)).first()
    original = src.enabled
    updated = sources_service.set_enabled(session, src.id, not original)
    assert updated is not None
    assert updated.enabled == (not original)
    sources_service.set_enabled(session, src.id, original)


def test_set_enabled_unknown_returns_none(session):
    assert sources_service.set_enabled(session, 999999, True) is None


def test_source_features_geolocated(session):
    features = map_service.get_source_features(session)
    assert features, "Debe haber fuentes situadas en el mapa"
    # Toda fuente situada tiene coordenadas y un color de estado.
    for f in features:
        assert f["latitude"] is not None and f["longitude"] is not None
        assert f["color"].startswith("#")
        assert f["level"] in {"nacional", "autonómica"}
    # Las autonómicas deben caer en territorio español aproximado.
    autonomicas = [f for f in features if f["level"] == "autonómica"]
    assert autonomicas
    for f in autonomicas:
        assert 27.0 <= f["latitude"] <= 44.5
