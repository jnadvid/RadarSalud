"""Carga del catálogo de fuentes (data/sources_catalog.yml)."""
from __future__ import annotations

from functools import lru_cache
from typing import Any

import yaml

from radarsalud.config import get_settings
from radarsalud.utils.logging import get_logger

logger = get_logger(__name__)


@lru_cache
def load_catalog() -> list[dict[str, Any]]:
    """Lee el catálogo YAML y devuelve una lista plana de entradas de fuente."""
    path = get_settings().sources_catalog_path
    if not path.exists():
        logger.warning("Catálogo de fuentes no encontrado en %s", path)
        return []
    with path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    entries: list[dict[str, Any]] = []
    for section in ("national", "autonomous_communities"):
        for item in data.get(section, []) or []:
            entry = dict(item)
            entry.setdefault("scope", section)
            entries.append(entry)
    return entries


def clear_catalog_cache() -> None:
    load_catalog.cache_clear()
