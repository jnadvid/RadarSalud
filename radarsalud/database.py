"""Capa de base de datos: motor SQLAlchemy, sesión y Base declarativa."""
from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import create_engine
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


def init_db() -> None:
    """Crea las carpetas de datos y todas las tablas si no existen."""
    get_settings().ensure_dirs()
    # Importa los modelos para que queden registrados en Base.metadata.
    from radarsalud import models  # noqa: F401  (efecto secundario de registro)

    Base.metadata.create_all(bind=engine)


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
