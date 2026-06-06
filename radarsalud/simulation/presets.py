"""Presets de simulación listos para usar desde la UI, API y CLI."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Preset:
    name: str
    label: str
    event: str
    province: str | None
    autonomous_community: str | None
    severity: str
    days: int
    multiplier: float
    description: str


PRESETS: dict[str, Preset] = {
    "gripe_madrid": Preset(
        name="gripe_madrid",
        label="Brote de gripe en Madrid",
        event="gripe",
        province="Madrid",
        autonomous_community="Madrid",
        severity="high",
        days=21,
        multiplier=3.0,
        description="Aumento estacional acelerado de actividad gripal en Madrid.",
    ),
    "covid_barcelona": Preset(
        name="covid_barcelona",
        label="Aumento de COVID-19 en Barcelona",
        event="covid",
        province="Barcelona",
        autonomous_community="Cataluña",
        severity="medium",
        days=18,
        multiplier=2.5,
        description="Repunte de positividad de SARS-CoV-2 en Barcelona.",
    ),
    "gastro_valencia": Preset(
        name="gastro_valencia",
        label="Gastroenteritis en Valencia",
        event="gastroenteritis",
        province="Valencia",
        autonomous_community="Comunidad Valenciana",
        severity="medium",
        days=10,
        multiplier=2.8,
        description="Brote de gastroenteritis aguda en el área de Valencia.",
    ),
    "calor_sevilla": Preset(
        name="calor_sevilla",
        label="Golpe de calor en Sevilla",
        event="golpe_calor",
        province="Sevilla",
        autonomous_community="Andalucía",
        severity="high",
        days=7,
        multiplier=4.0,
        description="Episodio de altas temperaturas y patología por calor en Sevilla.",
    ),
    "vrs_zaragoza": Preset(
        name="vrs_zaragoza",
        label="VRS en Zaragoza",
        event="vrs",
        province="Zaragoza",
        autonomous_community="Aragón",
        severity="high",
        days=21,
        multiplier=3.5,
        description="Circulación intensa de VRS con presión asistencial pediátrica.",
    ),
    "multi_evento": Preset(
        name="multi_evento",
        label="Evento multifuente en varias provincias",
        event="multi_evento",
        province=None,
        autonomous_community=None,
        severity="high",
        days=14,
        multiplier=3.0,
        description="Señales simultáneas de gripe, COVID-19 y VRS en varias provincias.",
    ),
}


def get_preset(name: str) -> Preset | None:
    return PRESETS.get(name)


def list_presets() -> list[Preset]:
    return list(PRESETS.values())
