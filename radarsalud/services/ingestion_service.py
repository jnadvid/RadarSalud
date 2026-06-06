"""Servicio de ingesta: siembra del catálogo, ejecución de conectores y CSV."""
from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from radarsalud.connectors import get_connector, get_connectors
from radarsalud.connectors.base import BaseConnector, ConnectorResult
from radarsalud.connectors.catalog import load_catalog
from radarsalud.connectors.csv_local import parse_csv
from radarsalud.models import IngestionRun, Observation, Source
from radarsalud.utils.logging import get_logger

logger = get_logger(__name__)

# Mapea el estado del catálogo al access_mode del modelo Source.
_ACCESS_MODE_MAP = {
    "operative": "open",
    "open": "open",
    "api_key_required": "api_key_required",
    "manual_download": "manual_download",
    "pending_verification": "pending_verification",
}


def seed_catalog(session: Session) -> int:
    """Crea o actualiza las fuentes a partir del catálogo YAML. Devuelve nº fuentes."""
    count = 0
    for entry in load_catalog():
        name = entry.get("name")
        if not name:
            continue
        access_mode = _ACCESS_MODE_MAP.get(entry.get("access_mode", "pending_verification"),
                                           "pending_verification")
        enabled = entry.get("access_mode") in {"operative", "open"}
        source = session.scalar(select(Source).where(Source.name == name))
        if source is None:
            source = Source(name=name)
            session.add(source)
        source.source_type = entry.get("source_type", "api")
        source.category = entry.get("category", "otro")
        source.url = entry.get("url")
        source.organization = entry.get("organization")
        source.license = entry.get("license")
        source.access_mode = access_mode
        source.refresh_frequency = entry.get("refresh_frequency")
        source.enabled = bool(enabled)
        source.notes = entry.get("notes")
        source.is_real_source = bool(entry.get("is_real_source", True))
        source.autonomous_community = entry.get("autonomous_community")
        count += 1
    session.commit()
    logger.info("Catálogo sembrado: %d fuentes", count)
    return count


def get_or_create_source(session: Session, name: str, **defaults: Any) -> Source:
    source = session.scalar(select(Source).where(Source.name == name))
    if source is None:
        source = Source(name=name, **defaults)
        session.add(source)
        session.flush()
    return source


def _store_discovered_datasets(session: Session, metadata: list[dict[str, Any]]) -> None:
    """Guarda metadatos de datasets descubiertos como fuentes pendientes."""
    for ds in metadata[:100]:
        title = ds.get("title") or ds.get("identifier")
        if not title:
            continue
        name = f"dataset::{str(title)[:160]}"
        existing = session.scalar(select(Source).where(Source.name == name))
        if existing:
            continue
        session.add(
            Source(
                name=name,
                source_type="api",
                category="salud",
                url=ds.get("url"),
                organization=str(ds.get("publisher") or "datos.gob.es"),
                access_mode="pending_verification",
                enabled=False,
                is_real_source=True,
                notes=f"Dataset descubierto (término: {ds.get('term')}).",
            )
        )


def run_connector(session: Session, connector: BaseConnector) -> IngestionRun:
    """Ejecuta un conector, registra el run e inserta observaciones reales."""
    source = get_or_create_source(
        session,
        connector.name,
        source_type=connector.source_type,
        category=connector.category,
        url=connector.url,
        organization=connector.organization,
        license=connector.license,
        access_mode=connector.access_mode,
        is_real_source=True,
    )
    run = IngestionRun(source_id=source.id, status="running")
    session.add(run)
    session.flush()

    try:
        result: ConnectorResult = connector.fetch()
    except Exception as exc:  # noqa: BLE001
        logger.exception("Conector %s falló", connector.name)
        run.status = "failed"
        run.error_message = str(exc)
        run.finished_at = datetime.utcnow()
        session.commit()
        return run

    inserted = 0
    for obs in result.observations:
        raw = obs.pop("raw_payload_json", None)
        session.add(
            Observation(
                data_mode="real",
                source_id=source.id,
                raw_payload_json=json.dumps(raw, ensure_ascii=False) if raw else None,
                **_observation_fields(obs),
            )
        )
        inserted += 1

    if result.source_metadata:
        _store_discovered_datasets(session, result.source_metadata)

    run.status = result.status
    # 'records_found' refleja tanto observaciones como metadatos descubiertos.
    run.records_found = result.records_found + len(result.source_metadata)
    run.records_inserted = inserted
    run.error_message = result.message if result.status in {"failed", "skipped"} else None
    run.finished_at = datetime.utcnow()
    source.last_checked_at = datetime.utcnow()
    session.commit()
    logger.info(
        "Ingesta %s: %s (%d encontradas, %d insertadas)",
        connector.name, result.status, result.records_found, inserted,
    )
    return run


def _observation_fields(obs: dict[str, Any]) -> dict[str, Any]:
    """Filtra el dict de observación a las columnas válidas del modelo."""
    allowed = {
        "observed_at", "autonomous_community", "province", "municipality",
        "province_code", "municipality_code", "latitude", "longitude",
        "signal_type", "health_event", "pathogen", "value", "unit",
        "confidence_score", "normalized_payload_json",
    }
    return {k: v for k, v in obs.items() if k in allowed}


def run_source(session: Session, name: str) -> IngestionRun | None:
    connector = get_connector(name)
    if connector is None:
        logger.warning("Conector desconocido: %s", name)
        return None
    return run_connector(session, connector)


def run_all(session: Session) -> list[IngestionRun]:
    runs = []
    for connector in get_connectors():
        if not connector.is_available():
            # Igualmente registramos el intento como skipped para trazabilidad.
            runs.append(run_connector(session, connector))
            continue
        runs.append(run_connector(session, connector))
    return runs


def import_csv_content(session: Session, content: str, *, source_name: str | None = None) -> dict:
    """Importa un CSV agregado como observaciones manual_import.

    Devuelve un resumen con filas insertadas y errores de validación.
    """
    parsed = parse_csv(content)
    if not parsed.ok:
        return {
            "status": "rejected",
            "rows_total": parsed.rows_total,
            "inserted": 0,
            "errors": parsed.errors,
        }

    inserted = 0
    for obs in parsed.observations:
        sname = source_name or obs.get("source_name") or "import_csv_manual"
        source = get_or_create_source(
            session,
            str(sname),
            source_type="csv",
            category="otro",
            access_mode="manual_download",
            organization="Importación manual",
            is_real_source=True,
        )
        session.add(
            Observation(
                data_mode="manual_import",
                source_id=source.id,
                observed_at=obs["observed_at"],
                autonomous_community=obs.get("autonomous_community"),
                province=obs.get("province"),
                municipality=obs.get("municipality"),
                province_code=obs.get("province_code"),
                signal_type=obs.get("signal_type"),
                health_event=obs.get("health_event"),
                pathogen=obs.get("pathogen"),
                value=obs.get("value"),
                unit=obs.get("unit"),
                confidence_score=obs.get("confidence_score"),
            )
        )
        inserted += 1
    session.commit()
    return {
        "status": "ok",
        "rows_total": parsed.rows_total,
        "inserted": inserted,
        "errors": [],
    }
