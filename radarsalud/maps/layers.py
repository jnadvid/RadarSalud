"""Definición de capas y colores del mapa."""
from __future__ import annotations

# Color por severidad (marcadores).
SEVERITY_COLORS = {
    "low": "#2ecc71",       # verde
    "medium": "#f1c40f",    # amarillo
    "high": "#e67e22",      # naranja
    "critical": "#e74c3c",  # rojo
}

# Capas temáticas por evento sanitario + capas por modo.
EVENT_LAYERS = {
    "gripe": "Gripe",
    "covid": "COVID-19",
    "vrs": "VRS",
    "gastroenteritis": "Gastroenteritis",
    "golpe_calor": "Golpe de calor",
    "calor_extremo": "Calor extremo",
    "calidad_aire": "Calidad del aire",
}

MODE_LAYERS = {
    "real": "Datos reales",
    "simulation": "Simulación",
}


def color_for_severity(severity: str) -> str:
    return SEVERITY_COLORS.get(severity, "#3498db")


def layer_name(health_event: str | None) -> str:
    if not health_event:
        return "Otros"
    return EVENT_LAYERS.get(health_event, health_event.capitalize())
