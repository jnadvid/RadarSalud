"""Tests de la detección de anomalías."""
from __future__ import annotations

from datetime import datetime, timedelta

import pandas as pd

from radarsalud.analytics.anomalies import detect_anomalies
from radarsalud.analytics.baseline import compute_baseline, percent_increase, robust_z


def _series_df(values: list[float]) -> pd.DataFrame:
    base = datetime(2026, 1, 1)
    return pd.DataFrame(
        {
            "observed_at": [base + timedelta(days=i) for i in range(len(values))],
            "province": ["Madrid"] * len(values),
            "autonomous_community": ["Madrid"] * len(values),
            "health_event": ["gripe"] * len(values),
            "signal_type": ["incidencia"] * len(values),
            "value": values,
            "source_id": [1] * len(values),
        }
    )


def test_detects_spike():
    df = _series_df([40, 42, 41, 39, 43, 40, 41, 200])
    results = detect_anomalies(df, data_mode="real")
    assert len(results) == 1
    r = results[0]
    assert r.province == "Madrid"
    assert r.health_event == "gripe"
    assert r.severity in {"medium", "high", "critical"}
    assert "no es diagnóstico" in r.explanation


def test_no_anomaly_on_flat_series():
    df = _series_df([40, 41, 39, 40, 41, 40, 39, 41])
    results = detect_anomalies(df, data_mode="real")
    assert results == []


def test_too_few_points():
    df = _series_df([40, 200])
    assert detect_anomalies(df, data_mode="real") == []


def test_baseline_and_helpers():
    stats = compute_baseline([10, 10, 10, 10, 50])
    assert stats.median == 10
    assert robust_z(50, stats.median, stats.mad) != 0 or stats.mad == 0
    assert percent_increase(20, 10) == 100.0
    assert percent_increase(5, 0) == float("inf")
