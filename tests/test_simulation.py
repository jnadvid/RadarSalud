"""Tests del modo simulación y su separación de los datos reales."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, select

from radarsalud.models import Alert, Observation
from radarsalud.services import simulation_service


def _count(session, model, **filters):
    stmt = select(func.count()).select_from(model)
    for k, v in filters.items():
        stmt = stmt.where(getattr(model, k) == v)
    return session.scalar(stmt) or 0


def test_simulation_does_not_touch_real_data(session):
    # Inserta una observación real "centinela".
    real_obs = Observation(
        data_mode="real", observed_at=datetime(2026, 1, 1), province="Madrid",
        health_event="gripe", signal_type="incidencia", value=42.0,
    )
    session.add(real_obs)
    session.commit()
    real_before = _count(session, Observation, data_mode="real")

    result = simulation_service.run_simulation(
        session, event="gripe", province="Madrid", severity="high", days=14, multiplier=3.0,
        seed=1,
    )
    assert result["observations_created"] > 0

    sim_obs = _count(session, Observation, data_mode="simulation")
    assert sim_obs >= result["observations_created"]
    # Los datos reales no cambian.
    assert _count(session, Observation, data_mode="real") == real_before

    # Las alertas simuladas están marcadas como simulation.
    sim_alerts = session.scalars(
        select(Alert).where(Alert.data_mode == "simulation")
    ).all()
    assert all(a.data_mode == "simulation" for a in sim_alerts)
    assert any("SIMULACIÓN" in (a.explanation or "") for a in sim_alerts)


def test_clear_simulations_removes_only_sim(session):
    simulation_service.run_simulation(
        session, event="covid", province="Barcelona", severity="medium", days=10, seed=2,
    )
    assert _count(session, Observation, data_mode="simulation") > 0
    real_before = _count(session, Observation, data_mode="real")

    res = simulation_service.clear_simulations(session)
    assert res["observations_deleted"] >= 0
    assert _count(session, Observation, data_mode="simulation") == 0
    # Real intacto.
    assert _count(session, Observation, data_mode="real") == real_before


def test_preset_runs(session):
    res = simulation_service.run_preset(session, "gripe_madrid", seed=3)
    assert res["observations_created"] == 21  # 21 días del preset
    simulation_service.clear_simulations(session)
