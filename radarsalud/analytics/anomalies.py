"""Detección de anomalías sobre series de observaciones agregadas.

Métodos combinados:
  - media móvil
  - z-score (media / desviación típica)
  - z-score robusto (mediana / MAD)
  - baseline histórico
  - subida porcentual respecto al periodo anterior

La detección es agnóstica al `data_mode`: el llamante filtra antes las
observaciones de un único modo (real, simulation) para no mezclar señales.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from radarsalud.analytics.baseline import (
    compute_baseline,
    percent_increase,
    robust_z,
    safe_z,
)
from radarsalud.analytics.explanations import build_explanation, build_recommendation
from radarsalud.analytics.severity import severity_from_score


@dataclass
class AnomalyResult:
    province: str | None
    autonomous_community: str | None
    health_event: str | None
    signal_type: str | None
    observed_at: object
    observed_value: float
    baseline_value: float
    deviation_score: float
    percent_rise: float
    method: str
    severity: str
    explanation: str
    recommendation: str
    source_ids: list[int] = field(default_factory=list)


# Umbrales de disparo (cualquiera que se cumpla activa la alerta).
Z_THRESHOLD = 2.5
ROBUST_Z_THRESHOLD = 3.5
PERCENT_THRESHOLD = 50.0
MIN_POINTS = 3


def detect_anomalies(
    df: pd.DataFrame,
    *,
    data_mode: str = "real",
    min_points: int = MIN_POINTS,
) -> list[AnomalyResult]:
    """Detecta anomalías en un DataFrame de observaciones.

    Columnas esperadas: observed_at, province, autonomous_community,
    health_event, signal_type, value, source_id.
    Agrupa por (province, health_event, signal_type) y evalúa el último punto.
    """
    if df.empty:
        return []

    required = {"observed_at", "value"}
    if not required.issubset(df.columns):
        return []

    results: list[AnomalyResult] = []
    group_cols = ["province", "health_event", "signal_type"]
    for _, group in df.groupby(group_cols, dropna=False):
        g = group.sort_values("observed_at")
        values = [float(v) for v in g["value"].tolist() if v is not None and pd.notna(v)]
        if len(values) < min_points:
            continue

        stats = compute_baseline(values)
        current = values[-1]

        z = safe_z(current, stats.mean, stats.std)
        rz = robust_z(current, stats.median, stats.mad)
        rise = percent_increase(current, stats.previous_period_mean)

        # ¿Hay anomalía al alza? (vigilancia de incrementos)
        triggered_method = None
        deviation = 0.0
        if rz >= ROBUST_Z_THRESHOLD:
            triggered_method, deviation = "z_robusto_mediana_mad", rz
        elif z >= Z_THRESHOLD:
            triggered_method, deviation = "z_score", z
        elif rise >= PERCENT_THRESHOLD:
            triggered_method, deviation = "subida_porcentual", rise / 50.0
        elif current > stats.moving_average * 1.5 and stats.moving_average > 0:
            triggered_method, deviation = "media_movil", current / max(stats.moving_average, 1e-9)

        if triggered_method is None:
            continue

        last_row = g.iloc[-1]
        province = last_row.get("province")
        community = last_row.get("autonomous_community")
        health_event = last_row.get("health_event")
        signal_type = last_row.get("signal_type")
        severity = severity_from_score(deviation, rise)

        source_ids = []
        if "source_id" in g.columns:
            source_ids = sorted(
                {int(s) for s in g["source_id"].dropna().tolist()} if len(g) else set()
            )

        explanation = build_explanation(
            health_event=health_event,
            province=province,
            observed_value=current,
            baseline_value=stats.median,
            method=triggered_method,
            deviation_score=deviation,
            percent_rise=rise,
            data_mode=data_mode,
        )
        recommendation = build_recommendation(health_event, data_mode)

        results.append(
            AnomalyResult(
                province=province,
                autonomous_community=community,
                health_event=health_event,
                signal_type=signal_type,
                observed_at=last_row.get("observed_at"),
                observed_value=current,
                baseline_value=stats.median,
                deviation_score=float(deviation),
                percent_rise=float(rise) if rise != float("inf") else 999.0,
                method=triggered_method,
                severity=severity,
                explanation=explanation,
                recommendation=recommendation,
                source_ids=source_ids,
            )
        )

    return results
