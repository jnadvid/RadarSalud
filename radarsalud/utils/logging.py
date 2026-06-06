"""Configuración de logging para RadarSalud."""
from __future__ import annotations

import logging

from radarsalud.config import get_settings

_CONFIGURED = False


def configure_logging() -> None:
    """Configura el logging raíz una sola vez."""
    global _CONFIGURED
    if _CONFIGURED:
        return
    level = getattr(logging, get_settings().log_level.upper(), logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    """Devuelve un logger con la configuración aplicada."""
    configure_logging()
    return logging.getLogger(name)
