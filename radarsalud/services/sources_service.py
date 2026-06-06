"""Servicio de fuentes: comprobación de disponibilidad y activación/desactivación.

La comprobación es "educada": identifica el agente, usa timeouts cortos y no
realiza scraping. Solo verifica que la URL responde (código < 400). No descarga
ni interpreta el contenido.
"""
from __future__ import annotations

from datetime import datetime

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from radarsalud.models import Source
from radarsalud.utils.http import polite_get
from radarsalud.utils.logging import get_logger

logger = get_logger(__name__)


def check_source(session: Session, source: Source, *, timeout: int = 8) -> dict:
    """Comprueba una fuente concreta y guarda el resultado en el registro."""
    source.last_checked_at = datetime.utcnow()

    if not source.url:
        source.last_check_ok = None
        source.last_check_http_status = None
        source.last_check_message = "Sin URL verificable (pendiente de verificación)."
        return {"id": source.id, "name": source.name, "ok": None, "status": None,
                "message": source.last_check_message}

    try:
        resp = polite_get(source.url, timeout=timeout)
        ok = resp.status_code < 400
        source.last_check_ok = ok
        source.last_check_http_status = resp.status_code
        source.last_check_message = (
            f"HTTP {resp.status_code}" if ok else f"HTTP {resp.status_code} (no disponible)"
        )
    except httpx.HTTPError as exc:
        source.last_check_ok = False
        source.last_check_http_status = None
        source.last_check_message = f"Error de red: {type(exc).__name__}"
    except Exception as exc:  # noqa: BLE001
        source.last_check_ok = False
        source.last_check_http_status = None
        source.last_check_message = f"Error: {exc}"

    return {
        "id": source.id,
        "name": source.name,
        "ok": source.last_check_ok,
        "status": source.last_check_http_status,
        "message": source.last_check_message,
    }


def check_all_sources(session: Session, *, include_datasets: bool = False,
                      timeout: int = 8) -> dict:
    """Comprueba todas las fuentes con URL. Marca las que no funcionan.

    Por defecto omite los datasets descubiertos (name 'dataset::...') para no
    lanzar cientos de peticiones; pásese include_datasets=True para incluirlos.
    """
    stmt = select(Source)
    if not include_datasets:
        stmt = stmt.where(~Source.name.like("dataset::%"))
    sources = session.scalars(stmt).all()

    results = []
    ok = down = nocheck = 0
    for source in sources:
        r = check_source(session, source, timeout=timeout)
        results.append(r)
        if r["ok"] is True:
            ok += 1
        elif r["ok"] is False:
            down += 1
        else:
            nocheck += 1
    session.commit()
    logger.info("Comprobación de fuentes: %d ok, %d caídas, %d sin URL", ok, down, nocheck)
    return {
        "checked": len(results),
        "reachable": ok,
        "down": down,
        "not_checkable": nocheck,
        "results": results,
    }


def set_enabled(session: Session, source_id: int, enabled: bool) -> Source | None:
    """Activa o desactiva una fuente (toggle)."""
    source = session.get(Source, source_id)
    if source is None:
        return None
    source.enabled = enabled
    session.commit()
    return source
