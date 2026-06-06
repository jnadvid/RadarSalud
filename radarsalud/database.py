"""Capa de base de datos: motor SQLAlchemy, sesión y Base declarativa."""
from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from radarsalud.config import get_settings


class Base(DeclarativeBase):
    """Base declarativa común para todos los modelos."""


_settings = get_settings()

# `check_same_thread=False` permite usar la sesión desde FastAPI/uvicorn.
_connect_args = {"check_same_thread": False} if _settings.database_url.startswith("sqlite") else {}

engine = create_engine(
    _settings.database_url,
    echo=False,
    future=True,
    connect_args=_connect_args,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


# Columnas añadidas tras la versión inicial. Mini-migración para SQLite: añade
# las que falten sin perder datos (SQLite soporta ALTER TABLE ADD COLUMN).
_LIGHTWEIGHT_MIGRATIONS: dict[str, dict[str, str]] = {
    "sources": {
        "autonomous_community": "VARCHAR(100)",
        "last_check_ok": "BOOLEAN",
        "last_check_http_status": "INTEGER",
        "last_check_message": "TEXT",
    },
}


def _run_lightweight_migrations() -> None:
    """Añade columnas nuevas a tablas existentes (idempotente)."""
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())
    with engine.begin() as conn:
        for table, columns in _LIGHTWEIGHT_MIGRATIONS.items():
            if table not in existing_tables:
                continue
            present = {c["name"] for c in inspector.get_columns(table)}
            for col, coltype in columns.items():
                if col not in present:
                    conn.execute(text(f'ALTER TABLE {table} ADD COLUMN {col} {coltype}'))


def init_db() -> None:
    """Crea las carpetas de datos y todas las tablas si no existen."""
    get_settings().ensure_dirs()
    # Importa los modelos para que queden registrados en Base.metadata.
    from radarsalud import models  # noqa: F401  (efecto secundario de registro)

    Base.metadata.create_all(bind=engine)
    _run_lightweight_migrations()


def get_session() -> Iterator[Session]:
    """Dependencia FastAPI: cede una sesión y la cierra al terminar."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@contextmanager
def session_scope() -> Iterator[Session]:
    """Contexto transaccional para uso fuera de FastAPI (CLI, servicios)."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
