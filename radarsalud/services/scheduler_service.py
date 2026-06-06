"""Programador (APScheduler) para actualizar datos reales automáticamente.

Ejecuta el pipeline (ingesta real + análisis) cada N horas. Es opcional: por
defecto está desactivado y puede arrancarse/pararse desde la API o la UI, o
activarse al inicio con RADARSALUD_SCHEDULER_ENABLED=true.
"""
from __future__ import annotations

from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler

from radarsalud.services import pipeline_service
from radarsalud.utils.logging import get_logger

logger = get_logger(__name__)

_JOB_ID = "auto_refresh"
_scheduler: BackgroundScheduler | None = None
_config: dict = {"hours": 12.0, "include_heavy": True}


def _get_scheduler() -> BackgroundScheduler:
    global _scheduler
    if _scheduler is None:
        _scheduler = BackgroundScheduler(daemon=True)
        _scheduler.start()
    return _scheduler


def _job() -> None:
    logger.info("Scheduler: lanzando actualización automática de datos reales")
    pipeline_service.start_refresh(
        include_light=True, include_heavy=_config["include_heavy"]
    )


def start(hours: float = 12.0, include_heavy: bool = True) -> dict:
    """Programa (o reprograma) la actualización automática cada `hours` horas."""
    hours = max(0.1, float(hours))
    _config["hours"] = hours
    _config["include_heavy"] = bool(include_heavy)
    sched = _get_scheduler()
    sched.add_job(
        _job,
        trigger="interval",
        hours=hours,
        id=_JOB_ID,
        replace_existing=True,
        next_run_time=datetime.now(),  # primera ejecución inmediata
        coalesce=True,
        max_instances=1,
    )
    logger.info("Scheduler activado: cada %.2f h (heavy=%s)", hours, include_heavy)
    return status()


def stop() -> dict:
    """Detiene la actualización automática (sin parar el resto de la app)."""
    if _scheduler is not None and _scheduler.get_job(_JOB_ID):
        _scheduler.remove_job(_JOB_ID)
        logger.info("Scheduler desactivado")
    return status()


def status() -> dict:
    job = _scheduler.get_job(_JOB_ID) if _scheduler else None
    next_run = None
    if job is not None and job.next_run_time:
        next_run = job.next_run_time.isoformat()
    return {
        "enabled": job is not None,
        "hours": _config["hours"],
        "include_heavy": _config["include_heavy"],
        "next_run": next_run,
    }
