"""Asignación de severidad a partir de la puntuación de desviación."""
from __future__ import annotations

SEVERITY_ORDER = ("low", "medium", "high", "critical")


def severity_from_score(deviation_score: float, percent_rise: float) -> str:
    """Clasifica la severidad combinando z-score robusto y subida porcentual.

    Reglas conservadoras pensadas para vigilancia poblacional, no para
    diagnóstico. Devuelve low/medium/high/critical.
    """
    score = abs(deviation_score)
    rise = percent_rise if percent_rise != float("inf") else 999.0

    if score >= 6 or rise >= 200:
        return "critical"
    if score >= 4 or rise >= 100:
        return "high"
    if score >= 2.5 or rise >= 50:
        return "medium"
    return "low"


def severity_rank(severity: str) -> int:
    try:
        return SEVERITY_ORDER.index(severity)
    except ValueError:
        return 0
