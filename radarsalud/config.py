"""Configuración central de RadarSalud, cargada desde entorno / .env."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Raíz del proyecto (carpeta que contiene `radarsalud/` y `data/`).
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"


def _alias(*names: str) -> AliasChoices:
    """Acepta varios nombres de variable de entorno para un mismo campo."""
    return AliasChoices(*names)


class Settings(BaseSettings):
    """Parámetros de configuración. Todos tienen valores por defecto seguros."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
        populate_by_name=True,
    )

    # Base de datos
    database_url: str = Field(
        default=f"sqlite:///{(DATA_DIR / 'radarsalud.sqlite').as_posix()}",
        validation_alias=_alias("RADARSALUD_DATABASE_URL", "database_url"),
    )

    # Servidor
    host: str = Field(default="127.0.0.1", validation_alias=_alias("RADARSALUD_HOST", "host"))
    port: int = Field(default=8000, validation_alias=_alias("RADARSALUD_PORT", "port"))
    debug: bool = Field(default=False, validation_alias=_alias("RADARSALUD_DEBUG", "debug"))

    # Fuentes externas
    aemet_api_key: str = Field(
        default="", validation_alias=_alias("AEMET_API_KEY", "aemet_api_key")
    )
    datos_gob_base_url: str = Field(
        default="https://datos.gob.es/apidata",
        validation_alias=_alias("DATOS_GOB_BASE_URL", "datos_gob_base_url"),
    )

    # Red / cortesía
    http_timeout: int = Field(
        default=30, validation_alias=_alias("RADARSALUD_HTTP_TIMEOUT", "http_timeout")
    )
    http_rate_limit_seconds: float = Field(
        default=1.0,
        validation_alias=_alias("RADARSALUD_HTTP_RATE_LIMIT_SECONDS", "http_rate_limit_seconds"),
    )
    user_agent: str = Field(
        default="RadarSalud/0.1 (+https://github.com/jnadvid/radarsalud) open-data research",
        validation_alias=_alias("RADARSALUD_USER_AGENT", "user_agent"),
    )

    # Logging
    log_level: str = Field(
        default="INFO", validation_alias=_alias("RADARSALUD_LOG_LEVEL", "log_level")
    )

    # Scheduler (actualización automática de datos reales)
    scheduler_enabled: bool = Field(
        default=False, validation_alias=_alias("RADARSALUD_SCHEDULER_ENABLED", "scheduler_enabled")
    )
    scheduler_hours: float = Field(
        default=12.0, validation_alias=_alias("RADARSALUD_SCHEDULER_HOURS", "scheduler_hours")
    )
    scheduler_include_heavy: bool = Field(
        default=True,
        validation_alias=_alias("RADARSALUD_SCHEDULER_INCLUDE_HEAVY", "scheduler_include_heavy"),
    )

    # Rutas derivadas ----------------------------------------------------------
    @property
    def data_dir(self) -> Path:
        return DATA_DIR

    @property
    def raw_dir(self) -> Path:
        return DATA_DIR / "raw"

    @property
    def processed_dir(self) -> Path:
        return DATA_DIR / "processed"

    @property
    def geo_dir(self) -> Path:
        return DATA_DIR / "geo"

    @property
    def imports_dir(self) -> Path:
        return DATA_DIR / "imports"

    @property
    def simulations_dir(self) -> Path:
        return DATA_DIR / "simulations"

    @property
    def sources_catalog_path(self) -> Path:
        return DATA_DIR / "sources_catalog.yml"

    def ensure_dirs(self) -> None:
        """Crea las carpetas de datos si no existen."""
        for d in (
            self.data_dir,
            self.raw_dir,
            self.processed_dir,
            self.geo_dir,
            self.imports_dir,
            self.simulations_dir,
        ):
            d.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    """Devuelve una instancia cacheada de Settings."""
    return Settings()


settings = get_settings()
