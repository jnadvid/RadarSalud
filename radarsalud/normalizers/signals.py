"""Normalización de tipos de señal y eventos sanitarios + extracción de palabras clave."""
from __future__ import annotations

import unicodedata

# Palabras clave sanitarias -> evento canónico, para clasificar señales RSS/boletín.
HEALTH_KEYWORDS: dict[str, str] = {
    "gripe": "gripe",
    "influenza": "gripe",
    "gripal": "gripe",
    "covid": "covid",
    "coronavirus": "covid",
    "sars-cov-2": "covid",
    "sars cov 2": "covid",
    "vrs": "vrs",
    "virus respiratorio sincitial": "vrs",
    "sincitial": "vrs",
    "bronquiolitis": "vrs",
    "gastroenteritis": "gastroenteritis",
    "diarrea": "gastroenteritis",
    "norovirus": "gastroenteritis",
    "salmonella": "gastroenteritis",
    "golpe de calor": "golpe_calor",
    "ola de calor": "calor_extremo",
    "calor extremo": "calor_extremo",
    "temperaturas extremas": "calor_extremo",
    "calidad del aire": "calidad_aire",
    "contaminacion": "calidad_aire",
    "ozono": "calidad_aire",
    "particulas": "calidad_aire",
    "infeccion respiratoria": "infeccion_respiratoria_aguda",
    "iras": "infeccion_respiratoria_aguda",
    "mortalidad": "mortalidad",
    "urgencias": "urgencias",
    "brote": "otro",
    "epidemia": "otro",
    "vigilancia epidemiologica": "otro",
}


def _strip_accents(text: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn"
    )


def detect_health_events(text: str) -> list[str]:
    """Detecta eventos sanitarios mencionados en un texto libre (RSS, boletín)."""
    if not text:
        return []
    normalized = _strip_accents(text).lower()
    found: list[str] = []
    for keyword, event in HEALTH_KEYWORDS.items():
        if _strip_accents(keyword).lower() in normalized and event not in found:
            found.append(event)
    return found


def extract_keywords(text: str) -> list[str]:
    """Devuelve las palabras clave sanitarias presentes en el texto."""
    if not text:
        return []
    normalized = _strip_accents(text).lower()
    return [kw for kw in HEALTH_KEYWORDS if _strip_accents(kw).lower() in normalized]
