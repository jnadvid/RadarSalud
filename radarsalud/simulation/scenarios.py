"""Definición de escenarios de simulación por tipo de evento.

Cada escenario describe la señal típica, su unidad, una línea base plausible y
el patógeno asociado. Los valores son ilustrativos para pruebas y docencia,
NUNCA datos reales.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ScenarioProfile:
    scenario_type: str
    health_event: str
    signal_type: str
    pathogen: str | None
    unit: str
    baseline: float          # valor base diario aproximado
    peak_multiplier: float   # cuánto sube en el pico respecto a baseline
    noise: float             # ruido relativo (0-1)


SCENARIOS: dict[str, ScenarioProfile] = {
    "gripe": ScenarioProfile(
        scenario_type="gripe",
        health_event="gripe",
        signal_type="incidencia",
        pathogen="Influenza A/B",
        unit="tasa_100k",
        baseline=40.0,
        peak_multiplier=4.0,
        noise=0.15,
    ),
    "covid": ScenarioProfile(
        scenario_type="covid",
        health_event="covid",
        signal_type="positividad",
        pathogen="SARS-CoV-2",
        unit="%",
        baseline=5.0,
        peak_multiplier=3.5,
        noise=0.2,
    ),
    "vrs": ScenarioProfile(
        scenario_type="vrs",
        health_event="vrs",
        signal_type="ingresos",
        pathogen="Virus Respiratorio Sincitial",
        unit="casos",
        baseline=12.0,
        peak_multiplier=5.0,
        noise=0.2,
    ),
    "gastroenteritis": ScenarioProfile(
        scenario_type="gastroenteritis",
        health_event="gastroenteritis",
        signal_type="urgencias",
        pathogen="Norovirus",
        unit="casos",
        baseline=25.0,
        peak_multiplier=3.0,
        noise=0.25,
    ),
    "golpe_calor": ScenarioProfile(
        scenario_type="golpe_calor",
        health_event="golpe_calor",
        signal_type="urgencias",
        pathogen=None,
        unit="casos",
        baseline=3.0,
        peak_multiplier=6.0,
        noise=0.3,
    ),
}


def get_scenario(scenario_type: str) -> ScenarioProfile:
    """Devuelve el perfil de escenario, con gripe como valor por defecto."""
    return SCENARIOS.get(scenario_type, SCENARIOS["gripe"])
