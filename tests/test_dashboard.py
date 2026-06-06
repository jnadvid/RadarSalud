"""Tests del servicio de panel: resúmenes, series y top de exceso (sin red)."""
from __future__ import annotations

import json
from datetime import datetime, timedelta

from radarsalud.models import Observation
from radarsalud.services import dashboard_service


def _add_mortality(session, province, code, day, observed, expected):
    session.add(
        Observation(
            data_mode="real",
            observed_at=day,
            province=province,
            province_code=code,
            signal_type="mortalidad",
            health_event="mortalidad",
            value=observed,
            unit="defunciones",
            normalized_payload_json=json.dumps({"esperadas_base": expected, "q99": expected * 1.4}),
        )
    )


def test_summary_and_timeseries_and_excess(session):
    base = datetime(2026, 5, 1)
    # Madrid con exceso, Soria dentro de lo esperado, dos días.
    _add_mortality(session, "Madrid", "28", base, 100, 80)
    _add_mortality(session, "Madrid", "28", base + timedelta(days=1), 130, 85)
    _add_mortality(session, "Soria", "42", base, 10, 12)
    _add_mortality(session, "Soria", "42", base + timedelta(days=1), 11, 12)
    session.commit()

    summ = dashboard_service.summary(session)
    assert summ["observations_real"] >= 4
    assert summ["last_real_observation"].startswith("2026-05-02")

    ts = dashboard_service.mortality_timeseries(session)
    assert ts["labels"] == ["2026-05-01", "2026-05-02"]
    # Día 2: observada = 130 (Madrid) + 11 (Soria) = 141
    assert ts["observed"][1] == 141.0
    assert ts["expected"][1] == 97.0  # 85 + 12

    te = dashboard_service.top_excess(session, limit=5)
    provinces = [i["province"] for i in te["items"]]
    assert "Madrid" in provinces
    madrid = next(i for i in te["items"] if i["province"] == "Madrid")
    assert madrid["excess_pct"] > 0  # 130 vs 85 esperado
