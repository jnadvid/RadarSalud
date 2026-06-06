"""Motor que genera observaciones simuladas coherentes para un escenario.

Produce series temporales con forma de brote (subida hasta un pico y bajada),
ruido controlado y localización geográfica. No persiste nada: devuelve dicts
que el servicio de simulación marca con `data_mode = simulation`.
"""
from __future__ import annotations

import math
import random
from datetime import datetime, timedelta

from radarsalud.normalizers.geography import (
    PROVINCES,
    centroid,
    community_for_province,
    provinces_in_community,
)
from radarsalud.simulation.scenarios import ScenarioProfile, get_scenario

_SEVERITY_FACTOR = {"low": 1.0, "medium": 1.6, "high": 2.4, "critical": 3.2}


def _brote_curve(day_index: int, total_days: int) -> float:
    """Curva de brote normalizada (0..1): sube hasta ~70% del periodo y baja."""
    if total_days <= 1:
        return 1.0
    peak_at = total_days * 0.7
    # Campana asimétrica basada en gaussiana centrada en el pico.
    width = max(total_days / 4.0, 1.0)
    return math.exp(-((day_index - peak_at) ** 2) / (2 * width**2))


def _generate_series(
    profile: ScenarioProfile,
    province: str,
    severity: str,
    days: int,
    multiplier: float,
    rng: random.Random,
) -> list[dict]:
    """Genera la serie diaria de observaciones para una provincia y escenario."""
    community = community_for_province(province) or province
    coords = centroid(province) or (40.0, -3.7)
    sev_factor = _SEVERITY_FACTOR.get(severity, 1.6)
    peak_extra = (profile.peak_multiplier - 1.0) * sev_factor * multiplier

    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    start = today - timedelta(days=days - 1)

    observations: list[dict] = []
    for i in range(days):
        when = start + timedelta(days=i)
        curve = _brote_curve(i, days)
        base = profile.baseline
        value = base * (1.0 + peak_extra * curve)
        noise = 1.0 + rng.uniform(-profile.noise, profile.noise)
        value = max(0.0, value * noise)
        observations.append(
            {
                "observed_at": when,
                "autonomous_community": community,
                "province": province,
                "municipality": None,
                "latitude": coords[0],
                "longitude": coords[1],
                "signal_type": profile.signal_type,
                "health_event": profile.health_event,
                "pathogen": profile.pathogen,
                "value": round(value, 2),
                "unit": profile.unit,
                "confidence_score": 0.5,  # confianza moderada: dato simulado
            }
        )
    return observations


def generate_observations(
    *,
    event: str,
    province: str | None,
    autonomous_community: str | None,
    severity: str = "medium",
    days: int = 14,
    multiplier: float = 2.0,
    seed: int | None = None,
) -> list[dict]:
    """Genera todas las observaciones simuladas de una ejecución.

    - Evento concreto + provincia -> una serie.
    - Evento concreto + comunidad -> una serie por provincia de la comunidad.
    - multi_evento -> varias provincias con eventos diferentes.
    """
    rng = random.Random(seed)
    observations: list[dict] = []

    if event == "multi_evento":
        # Mezcla coherente: gripe + covid + vrs en provincias representativas.
        plan = [
            ("gripe", "Madrid"),
            ("covid", "Barcelona"),
            ("vrs", "Zaragoza"),
            ("gastroenteritis", "Valencia"),
            ("golpe_calor", "Sevilla"),
        ]
        for ev, prov in plan:
            profile = get_scenario(ev)
            observations.extend(
                _generate_series(profile, prov, severity, days, multiplier, rng)
            )
        return observations

    profile = get_scenario(event)

    target_provinces: list[str]
    if province:
        target_provinces = [province]
    elif autonomous_community:
        target_provinces = [p.name for p in provinces_in_community(autonomous_community)]
        if not target_provinces:
            target_provinces = [PROVINCES[0].name]
    else:
        # Sin localización: usa Madrid como provincia por defecto.
        target_provinces = ["Madrid"]

    for prov in target_provinces:
        observations.extend(
            _generate_series(profile, prov, severity, days, multiplier, rng)
        )
    return observations
