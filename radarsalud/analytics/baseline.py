"""Cálculo de líneas base (baseline) sobre series de observaciones."""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass
class BaselineStats:
    mean: float
    std: float
    median: float
    mad: float  # desviación absoluta mediana (escalada a sigma)
    moving_average: float
    previous_period_mean: float
    n: int


def compute_baseline(values: list[float], window: int = 7) -> BaselineStats:
    """Calcula estadísticos de baseline sobre una serie ordenada cronológicamente.

    El último valor de la serie se considera "actual"; el resto forma el
    histórico que define la normalidad esperada.
    """
    series = pd.Series([v for v in values if v is not None], dtype="float64")
    n = len(series)
    if n == 0:
        return BaselineStats(0, 0, 0, 0, 0, 0, 0)

    history = series.iloc[:-1] if n > 1 else series
    mean = float(history.mean())
    std = float(history.std(ddof=0)) if len(history) > 1 else 0.0
    median = float(history.median())
    mad_raw = float((history - median).abs().median()) if len(history) else 0.0
    # Escalado a sigma equivalente para distribuciones aprox. normales.
    mad = 1.4826 * mad_raw

    moving_average = float(series.tail(window).mean())

    # Media del periodo anterior (mitad previa de la serie) para subida %.
    if n >= 4:
        half = n // 2
        previous_period_mean = float(series.iloc[:half].mean())
    else:
        previous_period_mean = mean

    return BaselineStats(
        mean=mean,
        std=std,
        median=median,
        mad=mad,
        moving_average=moving_average,
        previous_period_mean=previous_period_mean,
        n=n,
    )


def percent_increase(current: float, reference: float) -> float:
    """Subida porcentual respecto a una referencia (evita división por cero)."""
    if reference == 0:
        return float("inf") if current > 0 else 0.0
    return (current - reference) / abs(reference) * 100.0


def safe_z(current: float, mean: float, std: float) -> float:
    if std == 0:
        return 0.0
    return (current - mean) / std


def robust_z(current: float, median: float, mad: float) -> float:
    if mad == 0:
        return 0.0
    return (current - median) / mad
