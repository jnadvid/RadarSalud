"""Conector de RSS institucionales (feedparser).

Lee feeds RSS/Atom de organismos públicos declarados como operativos en el
catálogo de fuentes (`data/sources_catalog.yml`, tipo `rss`, estado
`operative`). Convierte entradas con menciones sanitarias relevantes en
observaciones de tipo `rss_signal` / `institutional_notice`.

No usa prensa generalista como fuente principal y no inventa URLs: si no hay
feeds operativos en el catálogo, el conector se salta documentando el motivo.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

import feedparser

from radarsalud.connectors.base import BaseConnector, ConnectorResult
from radarsalud.connectors.catalog import load_catalog
from radarsalud.normalizers.dates import parse_date
from radarsalud.normalizers.signals import detect_health_events, extract_keywords
from radarsalud.utils.logging import get_logger

logger = get_logger(__name__)


class RssInstitucionalConnector(BaseConnector):
    name = "rss_institucional"
    category = "rss"
    source_type = "rss"
    operational = True
    requires_key = False
    access_mode = "open"
    organization = "Organismos públicos (varios)"
    url = None
    license = "Cada organismo (uso institucional abierto)"

    def _operative_feeds(self) -> list[dict[str, Any]]:
        feeds = []
        for entry in load_catalog():
            if entry.get("source_type") == "rss" and entry.get("access_mode") in {
                "operative",
                "open",
            } and entry.get("url"):
                feeds.append(entry)
        return feeds

    def fetch(self) -> ConnectorResult:
        feeds = self._operative_feeds()
        if not feeds:
            return ConnectorResult(
                status="skipped",
                message=(
                    "Sin feeds RSS marcados como operativos en el catálogo. "
                    "Añada URLs verificadas con access_mode 'operative' en "
                    "data/sources_catalog.yml para activar la ingesta."
                ),
            )

        observations: list[dict[str, Any]] = []
        errors: list[str] = []
        for feed in feeds:
            try:
                parsed = feedparser.parse(feed["url"])
            except Exception as exc:  # noqa: BLE001
                errors.append(f"{feed['name']}: {exc}")
                continue
            for entry in parsed.entries[:50]:
                title = getattr(entry, "title", "") or ""
                summary = getattr(entry, "summary", "") or ""
                text = f"{title}. {summary}"
                events = detect_health_events(text)
                if not events:
                    continue
                published = (
                    parse_date(getattr(entry, "published", None))
                    or parse_date(getattr(entry, "updated", None))
                    or datetime.utcnow()
                )
                for event in events:
                    observations.append(
                        {
                            "observed_at": published,
                            "autonomous_community": feed.get("autonomous_community"),
                            "province": feed.get("province"),
                            "signal_type": "institutional_notice",
                            "health_event": event,
                            "value": 1.0,
                            "unit": "menciones",
                            "confidence_score": 0.3,
                            "raw_payload_json": {
                                "title": title,
                                "link": getattr(entry, "link", None),
                                "keywords": extract_keywords(text),
                                "feed": feed["name"],
                            },
                        }
                    )

        status = "success" if observations else "partial"
        message = f"{len(observations)} señales RSS sanitarias."
        if errors:
            message += f" Errores: {'; '.join(errors[:3])}"
        return ConnectorResult(observations=observations, status=status, message=message)
