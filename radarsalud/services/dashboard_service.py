"""Servicio de panel: resúmenes y series temporales para los gráficos.

Calcula indicadores útiles para vigilancia de salud pública a partir de las
observaciones reales (p. ej. mortalidad MoMo): serie nacional observada vs.
esperada, provincias con mayor exceso y recuento de alertas por severidad.
"""
from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from radarsalud.models import Alert, Observation, Simulation, Source

_REAL_MODES = ("real", "manual_import")


def _payload_expected(obs: Observation) -> float | None:
    if not obs.normalized_payload_json:
        return None
    try:
        return json.loads(obs.normalized_payload_json).get("esperadas_base")
    except (ValueError, TypeError):
        return None


def summary(session: Session) -> dict[str, Any]:
    """Indicadores de cabecera del panel."""
    def count(model, *conds):
        stmt = select(func.count()).select_from(model)
        for c in conds:
            stmt = stmt.where(c)
        return int(session.scalar(stmt) or 0)

    last_real = session.scalar(
        select(func.max(Observation.observed_at)).where(Observation.data_mode.in_(_REAL_MODES))
    )

    severities = {"low": 0, "medium": 0, "high": 0, "critical": 0}
    rows = session.execute(
        select(Alert.severity, func.count())
        .where(Alert.data_mode == "real")
        .group_by(Alert.severity)
    ).all()
    for sev, n in rows:
        severities[sev] = int(n)

    sources_ok = count(Source, Source.last_check_ok.is_(True))
    sources_down = count(Source, Source.last_check_ok.is_(False))

    return {
        "updated_at": datetime.utcnow().isoformat(),
        "observations_real": count(Observation, Observation.data_mode.in_(_REAL_MODES)),
        "observations_sim": count(Observation, Observation.data_mode == "simulation"),
        "alerts_real": count(Alert, Alert.data_mode == "real"),
        "alerts_sim": count(Alert, Alert.data_mode == "simulation"),
        "sources": count(Source, ~Source.name.like("dataset::%")),
        "sources_reachable": sources_ok,
        "sources_down": sources_down,
        "simulations": count(Simulation),
        "last_real_observation": last_real.isoformat() if last_real else None,
        "alerts_by_severity": severities,
    }


def mortality_timeseries(session: Session) -> dict[str, Any]:
    """Serie nacional de mortalidad: observada vs. esperada por fecha.

    Agrega las provincias por día (suma de observadas y de esperadas).
    """
    obs = session.scalars(
        select(Observation).where(
            Observation.data_mode.in_(_REAL_MODES),
            Observation.signal_type == "mortalidad",
        )
    ).all()

    observed_by_day: dict[str, float] = defaultdict(float)
    expected_by_day: dict[str, float] = defaultdict(float)
    for o in obs:
        if o.observed_at is None or o.value is None:
            continue
        day = o.observed_at.date().isoformat()
        observed_by_day[day] += o.value
        exp = _payload_expected(o)
        if exp is not None:
            expected_by_day[day] += exp

    labels = sorted(observed_by_day.keys())
    return {
        "labels": labels,
        "observed": [round(observed_by_day[d], 1) for d in labels],
        "expected": [round(expected_by_day[d], 1) if d in expected_by_day else None
                     for d in labels],
        "unit": "defunciones/día (todas las provincias)",
    }


def province_timeseries(session: Session, province: str) -> dict[str, Any]:
    """Serie de mortalidad observada vs. esperada de UNA provincia."""
    obs = session.scalars(
        select(Observation)
        .where(
            Observation.data_mode.in_(_REAL_MODES),
            Observation.signal_type == "mortalidad",
            Observation.province == province,
        )
        .order_by(Observation.observed_at)
    ).all()

    labels, observed, expected = [], [], []
    for o in obs:
        if o.observed_at is None:
            continue
        labels.append(o.observed_at.date().isoformat())
        observed.append(o.value)
        expected.append(_payload_expected(o))

    latest_excess = None
    if observed and expected and observed[-1] is not None and expected[-1]:
        latest_excess = round((observed[-1] - expected[-1]) / expected[-1] * 100, 1)

    return {
        "province": province,
        "labels": labels,
        "observed": observed,
        "expected": expected,
        "points": len(labels),
        "latest_excess_pct": latest_excess,
        "unit": "defunciones/día",
    }


def top_excess(session: Session, limit: int = 10) -> dict[str, Any]:
    """Provincias con mayor exceso de mortalidad en su último dato disponible."""
    obs = session.scalars(
        select(Observation)
        .where(Observation.data_mode.in_(_REAL_MODES), Observation.signal_type == "mortalidad")
        .order_by(Observation.observed_at)
    ).all()

    latest: dict[str, Observation] = {}
    for o in obs:
        if o.province:
            latest[o.province] = o  # orden asc -> última gana

    items = []
    for prov, o in latest.items():
        expected = _payload_expected(o)
        if expected is None or o.value is None or expected <= 0:
            continue
        excess = o.value - expected
        items.append(
            {
                "province": prov,
                "observed": round(o.value, 1),
                "expected": round(expected, 1),
                "excess": round(excess, 1),
                "excess_pct": round(excess / expected * 100, 1),
                "date": o.observed_at.date().isoformat() if o.observed_at else None,
            }
        )
    items.sort(key=lambda x: x["excess_pct"], reverse=True)
    return {"items": items[:limit]}
