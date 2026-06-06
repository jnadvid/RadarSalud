"""Generación de explicaciones y recomendaciones legibles para las alertas.

Las explicaciones son descriptivas y poblacionales. No constituyen diagnóstico
ni recomendación clínica individual.
"""
from __future__ import annotations

_RECOMMENDATIONS = {
    "gripe": "Señal compatible con aumento de actividad gripal. Contrastar con la red "
             "centinela de vigilancia y reforzar medidas de prevención respiratoria.",
    "covid": "Posible incremento de transmisión de COVID-19. Revisar indicadores "
             "complementarios (aguas residuales, urgencias) antes de conclusiones.",
    "vrs": "Aumento compatible con circulación de VRS, relevante en menores y mayores. "
           "Verificar con vigilancia hospitalaria pediátrica.",
    "gastroenteritis": "Incremento de gastroenteritis aguda. Considerar investigación de "
                       "posible brote de origen alimentario o hídrico.",
    "golpe_calor": "Riesgo de patología por calor. Coordinar con planes de prevención de "
                   "altas temperaturas y avisos a población vulnerable.",
    "calor_extremo": "Episodio de calor extremo. Activar protocolos de protección a "
                     "personas vulnerables.",
    "calidad_aire": "Deterioro de la calidad del aire. Seguir recomendaciones de la "
                    "autoridad ambiental competente.",
}

_DEFAULT_RECOMMENDATION = (
    "Señal anómala detectada en datos abiertos agregados. Requiere validación por "
    "salud pública antes de cualquier actuación."
)


def build_explanation(
    *,
    health_event: str | None,
    province: str | None,
    observed_value: float | None,
    baseline_value: float | None,
    method: str,
    deviation_score: float,
    percent_rise: float,
    data_mode: str,
) -> str:
    """Construye una explicación textual de la anomalía detectada."""
    prefix = "[SIMULACIÓN] " if data_mode == "simulation" else ""
    ev = health_event or "señal"
    loc = province or "territorio"
    obs = "n/d" if observed_value is None else f"{observed_value:.2f}"
    base = "n/d" if baseline_value is None else f"{baseline_value:.2f}"
    rise_txt = "∞" if percent_rise == float("inf") else f"{percent_rise:.0f}%"
    return (
        f"{prefix}Anomalía de '{ev}' en {loc}: valor observado {obs} frente a baseline "
        f"{base} (método {method}, score {deviation_score:.2f}, subida {rise_txt}). "
        "Indicador poblacional sobre datos abiertos agregados; no es diagnóstico."
    )


def build_recommendation(health_event: str | None, data_mode: str) -> str:
    base = _RECOMMENDATIONS.get(health_event or "", _DEFAULT_RECOMMENDATION)
    if data_mode == "simulation":
        return "[SIMULACIÓN] " + base + " (Dato simulado: no representa una situación real.)"
    return base
