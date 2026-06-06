"""Configuración de pytest: usa una base SQLite temporal y aislada.

Importante: se fija la variable de entorno de la base ANTES de importar el
paquete `radarsalud`, para que el engine global apunte a la base temporal.
"""
from __future__ import annotations

import os
import tempfile

# Base temporal por sesión de tests (aislada de data/radarsalud.sqlite).
_DB_FD, _DB_PATH = tempfile.mkstemp(suffix="_radarsalud_test.sqlite")
os.close(_DB_FD)
os.environ["RADARSALUD_DATABASE_URL"] = f"sqlite:///{_DB_PATH}"

import pytest  # noqa: E402

from radarsalud.database import init_db, session_scope  # noqa: E402
from radarsalud.services import ingestion_service  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def _setup_database():
    """Crea las tablas y siembra el catálogo una vez por sesión."""
    init_db()
    with session_scope() as session:
        ingestion_service.seed_catalog(session)
    yield
    try:
        os.remove(_DB_PATH)
    except OSError:
        pass


@pytest.fixture
def session():
    """Sesión de base de datos para un test."""
    from radarsalud.database import SessionLocal

    s = SessionLocal()
    try:
        yield s
    finally:
        s.close()
