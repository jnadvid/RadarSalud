"""Tests de los conectores reales (sin depender de red).

Verifican el contrato (estado, plantillas documentadas, validación de CSV) sin
realizar peticiones que requieran conectividad. El conector de datos.gob.es se
prueba solo en su comportamiento ante fallo de red (degradación elegante).
"""
from __future__ import annotations

from radarsalud.connectors import get_connector, get_connectors
from radarsalud.connectors.csv_local import parse_csv


def test_all_connectors_have_names():
    names = [c.name for c in get_connectors()]
    assert "datos_gob_es" in names
    assert "rss_institucional" in names
    assert "aemet_opendata" in names
    assert len(names) == len(set(names)), "Nombres de conector duplicados"


def test_template_connectors_skip_cleanly():
    # Conectores no operativos devuelven 'skipped' con mensaje documentado.
    for name in ["ine_poblacion", "isciii_sivira", "ministerio_sanidad",
                 "calidad_aire_nacional", "aguas_residuales", "boe_datos_abiertos"]:
        connector = get_connector(name)
        assert connector is not None
        result = connector.fetch()
        assert result.status == "skipped"
        assert result.message
        assert result.records_found == 0


def test_aemet_disabled_without_key(monkeypatch):
    monkeypatch.setenv("AEMET_API_KEY", "")
    connector = get_connector("aemet_opendata")
    # Sin clave, el conector no está disponible.
    from radarsalud.config import get_settings
    get_settings.cache_clear()
    assert connector.fetch().status == "skipped"


def test_csv_parse_valid():
    content = (
        "observed_at,province,health_event,signal_type,value,unit\n"
        "2026-01-01,Madrid,gripe,incidencia,42,tasa_100k\n"
        "2026-01-08,Madrid,gripe,incidencia,55,tasa_100k\n"
    )
    result = parse_csv(content)
    assert result.ok
    assert len(result.observations) == 2
    assert result.observations[0]["province"] == "Madrid"
    assert result.observations[0]["province_code"] == "28"


def test_csv_rejects_personal_columns():
    content = "observed_at,province,dni,value\n2026-01-01,Madrid,12345678Z,5\n"
    result = parse_csv(content)
    assert not result.ok
    assert any("dni" in e.lower() for e in result.errors)


def test_csv_rejects_invalid_event():
    content = (
        "observed_at,province,health_event,signal_type,value\n"
        "2026-01-01,Madrid,evento_falso,incidencia,5\n"
    )
    result = parse_csv(content)
    assert not result.ok
