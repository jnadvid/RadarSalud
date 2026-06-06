"""Tests de la API FastAPI."""
from __future__ import annotations

import io

import pytest
from fastapi.testclient import TestClient

from radarsalud.main import app


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_web_pages(client):
    for path in ["/", "/map", "/simulation", "/sources", "/alerts",
                 "/province?name=Madrid", "/import"]:
        assert client.get(path).status_code == 200


def test_exports_csv(client):
    r = client.get("/api/v1/observations.csv?data_mode=real")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/csv")
    assert "observed_at" in r.text.splitlines()[0]
    r2 = client.get("/api/v1/alerts.csv")
    assert r2.status_code == 200
    assert "severity" in r2.text.splitlines()[0]


def test_province_timeseries_endpoint(client):
    r = client.get("/api/v1/dashboard/province_timeseries?province=Madrid")
    assert r.status_code == 200
    body = r.json()
    assert body["province"] == "Madrid"
    assert "observed" in body and "expected" in body


def test_scheduler_start_status_stop(client, monkeypatch):
    # Evita que el job real dispare el pipeline durante el test.
    monkeypatch.setattr("radarsalud.services.scheduler_service._job", lambda: None)
    r = client.post("/api/v1/scheduler/start", json={"hours": 24, "include_heavy": False})
    assert r.status_code == 200 and r.json()["enabled"] is True
    s = client.get("/api/v1/scheduler/status").json()
    assert s["enabled"] is True and s["hours"] == 24
    r2 = client.post("/api/v1/scheduler/stop")
    assert r2.json()["enabled"] is False


def test_alert_triage_roundtrip(client):
    # Crea alertas vía simulación, cambia el estado de una y limpia.
    client.post("/api/v1/simulation/run", json={
        "event": "gripe", "province": "Madrid", "severity": "high",
        "days": 14, "multiplier": 3.0,
    })
    alerts = client.get("/api/v1/alerts?data_mode=simulation").json()
    assert alerts
    aid = alerts[0]["id"]
    r = client.patch(f"/api/v1/alerts/{aid}/status", json={"status": "reviewed"})
    assert r.status_code == 200 and r.json()["status"] == "reviewed"
    client.post("/api/v1/simulation/clear")


def test_sources_endpoint(client):
    r = client.get("/api/v1/sources")
    assert r.status_code == 200
    assert isinstance(r.json(), list)
    assert len(r.json()) >= 20


def test_simulation_run_clear_flow(client):
    r = client.post("/api/v1/simulation/run", json={
        "event": "gripe", "province": "Madrid", "severity": "high",
        "days": 14, "multiplier": 3.0,
    })
    assert r.status_code == 200
    data = r.json()
    assert data["observations_created"] > 0

    # GeoJSON de simulación tiene features.
    gj = client.get("/api/v1/maps/alerts.geojson?mode=simulation").json()
    assert gj["type"] == "FeatureCollection"

    # Limpieza.
    rc = client.post("/api/v1/simulation/clear")
    assert rc.status_code == 200
    assert rc.json()["observations_deleted"] >= 0


def test_preset_unknown_returns_404(client):
    r = client.post("/api/v1/simulation/preset/no_existe")
    assert r.status_code == 404


def test_csv_upload_and_reject(client):
    good = (
        "observed_at,province,health_event,signal_type,value,unit\n"
        "2026-01-01,Madrid,gripe,incidencia,42,tasa_100k\n"
        "2026-01-08,Madrid,gripe,incidencia,90,tasa_100k\n"
    )
    files = {"file": ("good.csv", io.BytesIO(good.encode()), "text/csv")}
    r = client.post("/api/v1/uploads/csv", files=files)
    assert r.status_code == 200
    assert r.json()["inserted"] == 2

    bad = "observed_at,province,email,value\n2026-01-01,Madrid,a@b.com,5\n"
    files = {"file": ("bad.csv", io.BytesIO(bad.encode()), "text/csv")}
    r = client.post("/api/v1/uploads/csv", files=files)
    assert r.status_code == 422


def test_analytics_run(client):
    r = client.post("/api/v1/analytics/run", json={"data_mode": "real"})
    assert r.status_code == 200
    assert "alerts_created" in r.json()


def test_alert_status_update_404(client):
    r = client.patch("/api/v1/alerts/999999/status", json={"status": "reviewed"})
    assert r.status_code == 404
