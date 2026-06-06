"""Tests del mapa y la geografía."""
from __future__ import annotations

from radarsalud.maps.folium_map import render_map_html
from radarsalud.maps.spain_geojson import provinces_point_geojson
from radarsalud.normalizers.geography import (
    PROVINCES,
    centroid,
    normalize_province,
    province_code,
)


def test_provinces_complete():
    assert len(PROVINCES) == 52  # 50 provincias + Ceuta + Melilla


def test_province_normalization_and_codes():
    assert normalize_province("vizcaya") == "Bizkaia"
    assert normalize_province("LA CORUÑA") == "A Coruña"
    assert province_code("Madrid") == "28"
    assert centroid("Sevilla") is not None


def test_provinces_geojson():
    gj = provinces_point_geojson()
    assert gj["type"] == "FeatureCollection"
    assert len(gj["features"]) == 52


def test_render_map_with_alerts():
    alerts = [
        {
            "data_mode": "simulation",
            "health_event": "gripe",
            "province": "Madrid",
            "observed_at": "2026-01-15",
            "severity": "high",
            "observed_value": 180,
            "baseline_value": 40,
            "explanation": "test",
            "recommendation": "test",
            "source": "sim",
            "latitude": 40.42,
            "longitude": -3.70,
        }
    ]
    html = render_map_html(alerts)
    assert "<html" in html.lower()
    assert "leaflet" in html.lower() or "folium" in html.lower()
