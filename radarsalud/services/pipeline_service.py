"""Runner del pipeline en segundo plano: ingesta real + análisis.

Permite lanzar desde la interfaz web "actualizar datos reales" sin bloquear la
petición HTTP ni usar la CLI. Mantiene un estado en memoria que la UI consulta
por sondeo (polling).
"""
from __future__ import annotations

import threading
from datetime import datetime

from radarsalud.database import session_scope
from radarsalud.services import analytics_service, ingestion_service
from radarsalud.utils.logging import get_logger

logger = get_logger(__name__)

_lock = threading.Lock()
_state: dict = {
    "running": False,
    "step": "idle",
    "message": "Sin ejecuciones todavía.",
    "started_at": None,
    "finished_at": None,
    "result": None,
    "error": None,
}


def get_state() -> dict:
    with _lock:
        return dict(_state)


def _set(**kwargs) -> None:
    with _lock:
        _state.update(kwargs)


def _run(include_light: bool, include_heavy: bool) -> None:
    try:
        if include_light:
            _set(step="ingesta_ligera", message="Consultando catálogo y RSS abiertos…")
            with session_scope() as session:
                ingestion_service.run_all(session, include_heavy=False)

        if include_heavy:
            _set(step="mortalidad",
                 message="Descargando mortalidad real por provincia (ISCIII MoMo). "
                         "Puede tardar 30–90 s…")
            with session_scope() as session:
                run = ingestion_service.run_source(session, "isciii_momo")
                inserted = run.records_inserted if run else 0
            logger.info("Pipeline: MoMo insertó %s observaciones", inserted)

        _set(step="analisis", message="Detectando anomalías sobre los datos reales…")
        with session_scope() as session:
            summary = analytics_service.run_analysis(session, data_mode="real")

        _set(
            running=False,
            step="completado",
            message="✅ Datos reales actualizados y analizados.",
            finished_at=datetime.utcnow().isoformat(),
            result=summary,
            error=None,
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("Fallo en el pipeline")
        _set(
            running=False,
            step="error",
            message=f"❌ Error: {exc}",
            finished_at=datetime.utcnow().isoformat(),
            error=str(exc),
        )


def start_refresh(*, include_light: bool = True, include_heavy: bool = True) -> bool:
    """Arranca el pipeline en un hilo. Devuelve False si ya estaba en marcha."""
    with _lock:
        if _state["running"]:
            return False
        _state.update(
            running=True, step="iniciando", message="Iniciando actualización…",
            started_at=datetime.utcnow().isoformat(), finished_at=None,
            result=None, error=None,
        )
    thread = threading.Thread(target=_run, args=(include_light, include_heavy), daemon=True)
    thread.start()
    return True
