"""Cliente HTTP educado: User-Agent identificable y límite de frecuencia.

Respeta términos de uso razonables: identifica el agente, aplica un retardo
mínimo entre peticiones y un timeout. No realiza scraping agresivo.
"""
from __future__ import annotations

import time
from typing import Any

import httpx

from radarsalud.config import get_settings
from radarsalud.utils.logging import get_logger

logger = get_logger(__name__)

_last_request_at: dict[str, float] = {}


def _respect_rate_limit(host: str, min_interval: float) -> None:
    """Espera lo necesario para no superar el límite por host."""
    last = _last_request_at.get(host)
    now = time.monotonic()
    if last is not None:
        elapsed = now - last
        if elapsed < min_interval:
            time.sleep(min_interval - elapsed)
    _last_request_at[host] = time.monotonic()


def get_client(timeout: int | None = None) -> httpx.Client:
    """Crea un cliente httpx con cabeceras educadas."""
    s = get_settings()
    return httpx.Client(
        timeout=timeout or s.http_timeout,
        headers={"User-Agent": s.user_agent, "Accept": "*/*"},
        follow_redirects=True,
    )


def polite_get(url: str, *, params: dict[str, Any] | None = None,
               headers: dict[str, str] | None = None,
               timeout: int | None = None) -> httpx.Response:
    """GET con User-Agent, rate-limit por host y timeout.

    Lanza httpx.HTTPError en caso de fallo de red; el llamante decide cómo
    registrarlo (típicamente como ingestion_run fallido).
    """
    s = get_settings()
    host = httpx.URL(url).host or "unknown"
    _respect_rate_limit(host, s.http_rate_limit_seconds)
    merged_headers = {"User-Agent": s.user_agent, "Accept": "*/*"}
    if headers:
        merged_headers.update(headers)
    logger.debug("GET %s params=%s", url, params)
    with httpx.Client(timeout=timeout or s.http_timeout, follow_redirects=True) as client:
        response = client.get(url, params=params, headers=merged_headers)
    return response
