"""Geografía de referencia de España: provincias, CCAA y centroides.

Códigos de provincia según la codificación INE (2 dígitos). Los centroides son
aproximados (capital de provincia) y se usan únicamente para situar marcadores
en el mapa cuando la observación no aporta coordenadas propias.

Fuente de los códigos: codificación oficial de provincias del INE.
"""
from __future__ import annotations

import unicodedata
from dataclasses import dataclass


@dataclass(frozen=True)
class Province:
    code: str
    name: str
    autonomous_community: str
    latitude: float
    longitude: float


# code, name, comunidad autónoma, lat, lon
PROVINCES: list[Province] = [
    Province("01", "Álava", "País Vasco", 42.85, -2.67),
    Province("02", "Albacete", "Castilla-La Mancha", 38.99, -1.86),
    Province("03", "Alicante", "Comunidad Valenciana", 38.35, -0.48),
    Province("04", "Almería", "Andalucía", 36.84, -2.46),
    Province("05", "Ávila", "Castilla y León", 40.66, -4.70),
    Province("06", "Badajoz", "Extremadura", 38.88, -6.97),
    Province("07", "Baleares", "Baleares", 39.57, 2.65),
    Province("08", "Barcelona", "Cataluña", 41.39, 2.17),
    Province("09", "Burgos", "Castilla y León", 42.34, -3.70),
    Province("10", "Cáceres", "Extremadura", 39.47, -6.37),
    Province("11", "Cádiz", "Andalucía", 36.53, -6.29),
    Province("12", "Castellón", "Comunidad Valenciana", 39.99, -0.04),
    Province("13", "Ciudad Real", "Castilla-La Mancha", 38.99, -3.93),
    Province("14", "Córdoba", "Andalucía", 37.89, -4.78),
    Province("15", "A Coruña", "Galicia", 43.37, -8.40),
    Province("16", "Cuenca", "Castilla-La Mancha", 40.07, -2.13),
    Province("17", "Girona", "Cataluña", 41.98, 2.82),
    Province("18", "Granada", "Andalucía", 37.18, -3.60),
    Province("19", "Guadalajara", "Castilla-La Mancha", 40.63, -3.16),
    Province("20", "Gipuzkoa", "País Vasco", 43.32, -1.98),
    Province("21", "Huelva", "Andalucía", 37.26, -6.95),
    Province("22", "Huesca", "Aragón", 42.13, -0.41),
    Province("23", "Jaén", "Andalucía", 37.77, -3.79),
    Province("24", "León", "Castilla y León", 42.60, -5.57),
    Province("25", "Lleida", "Cataluña", 41.62, 0.62),
    Province("26", "La Rioja", "La Rioja", 42.46, -2.45),
    Province("27", "Lugo", "Galicia", 43.01, -7.56),
    Province("28", "Madrid", "Madrid", 40.42, -3.70),
    Province("29", "Málaga", "Andalucía", 36.72, -4.42),
    Province("30", "Murcia", "Murcia", 37.99, -1.13),
    Province("31", "Navarra", "Navarra", 42.81, -1.65),
    Province("32", "Ourense", "Galicia", 42.34, -7.86),
    Province("33", "Asturias", "Asturias", 43.36, -5.85),
    Province("34", "Palencia", "Castilla y León", 42.01, -4.53),
    Province("35", "Las Palmas", "Canarias", 28.12, -15.43),
    Province("36", "Pontevedra", "Galicia", 42.43, -8.64),
    Province("37", "Salamanca", "Castilla y León", 40.97, -5.66),
    Province("38", "Santa Cruz de Tenerife", "Canarias", 28.47, -16.25),
    Province("39", "Cantabria", "Cantabria", 43.46, -3.81),
    Province("40", "Segovia", "Castilla y León", 40.95, -4.12),
    Province("41", "Sevilla", "Andalucía", 37.39, -5.99),
    Province("42", "Soria", "Castilla y León", 41.76, -2.47),
    Province("43", "Tarragona", "Cataluña", 41.12, 1.25),
    Province("44", "Teruel", "Aragón", 40.34, -1.11),
    Province("45", "Toledo", "Castilla-La Mancha", 39.86, -4.02),
    Province("46", "Valencia", "Comunidad Valenciana", 39.47, -0.38),
    Province("47", "Valladolid", "Castilla y León", 41.65, -4.72),
    Province("48", "Bizkaia", "País Vasco", 43.26, -2.93),
    Province("49", "Zamora", "Castilla y León", 41.50, -5.74),
    Province("50", "Zaragoza", "Aragón", 41.65, -0.89),
    Province("51", "Ceuta", "Ceuta", 35.89, -5.31),
    Province("52", "Melilla", "Melilla", 35.29, -2.94),
]

PROVINCES_BY_CODE: dict[str, Province] = {p.code: p for p in PROVINCES}


def _strip_accents(text: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn"
    )


def _key(text: str) -> str:
    return _strip_accents(text).strip().lower()


# Alias frecuentes -> nombre canónico de provincia.
_PROVINCE_ALIASES: dict[str, str] = {}
for _p in PROVINCES:
    _PROVINCE_ALIASES[_key(_p.name)] = _p.name

# Variantes habituales de nombre.
_EXTRA_ALIASES = {
    "alava": "Álava",
    "araba": "Álava",
    "vizcaya": "Bizkaia",
    "guipuzcoa": "Gipuzkoa",
    "la coruna": "A Coruña",
    "coruna": "A Coruña",
    "la coruña": "A Coruña",
    "gerona": "Girona",
    "lerida": "Lleida",
    "orense": "Ourense",
    "illes balears": "Baleares",
    "islas baleares": "Baleares",
    "palma de mallorca": "Baleares",
    "santa cruz de tenerife": "Santa Cruz de Tenerife",
    "tenerife": "Santa Cruz de Tenerife",
    "las palmas de gran canaria": "Las Palmas",
    "castellon de la plana": "Castellón",
    "castello": "Castellón",
    "valencia/valència": "Valencia",
    "alacant": "Alicante",
    "asturias": "Asturias",
    "principado de asturias": "Asturias",
    "cantabria": "Cantabria",
    "navarra": "Navarra",
    "comunidad foral de navarra": "Navarra",
    "rioja": "La Rioja",
    "la rioja": "La Rioja",
    "madrid": "Madrid",
    "murcia": "Murcia",
    "region de murcia": "Murcia",
}
_PROVINCE_ALIASES.update({_key(k): v for k, v in _EXTRA_ALIASES.items()})


# Nombres canónicos de comunidades autónomas (para validación/agrupación).
AUTONOMOUS_COMMUNITIES: list[str] = sorted({p.autonomous_community for p in PROVINCES})

_CCAA_ALIASES = {
    "andalucia": "Andalucía",
    "aragon": "Aragón",
    "asturias": "Asturias",
    "principado de asturias": "Asturias",
    "baleares": "Baleares",
    "illes balears": "Baleares",
    "islas baleares": "Baleares",
    "canarias": "Canarias",
    "cantabria": "Cantabria",
    "castilla-la mancha": "Castilla-La Mancha",
    "castilla la mancha": "Castilla-La Mancha",
    "castilla y leon": "Castilla y León",
    "cataluna": "Cataluña",
    "cataluña": "Cataluña",
    "catalunya": "Cataluña",
    "comunidad valenciana": "Comunidad Valenciana",
    "comunitat valenciana": "Comunidad Valenciana",
    "valencia": "Comunidad Valenciana",
    "extremadura": "Extremadura",
    "galicia": "Galicia",
    "madrid": "Madrid",
    "comunidad de madrid": "Madrid",
    "murcia": "Murcia",
    "region de murcia": "Murcia",
    "navarra": "Navarra",
    "comunidad foral de navarra": "Navarra",
    "pais vasco": "País Vasco",
    "euskadi": "País Vasco",
    "la rioja": "La Rioja",
    "rioja": "La Rioja",
    "ceuta": "Ceuta",
    "melilla": "Melilla",
}


def normalize_province(name: str | None) -> str | None:
    """Devuelve el nombre canónico de provincia o None si no se reconoce."""
    if not name:
        return None
    return _PROVINCE_ALIASES.get(_key(name))


def normalize_community(name: str | None) -> str | None:
    """Devuelve el nombre canónico de comunidad autónoma o None."""
    if not name:
        return None
    return _CCAA_ALIASES.get(_key(name))


def province_code(name: str | None) -> str | None:
    """Código INE de la provincia a partir de su nombre (canónico o alias)."""
    canonical = normalize_province(name)
    if canonical is None:
        return None
    for p in PROVINCES:
        if p.name == canonical:
            return p.code
    return None


def community_for_province(name: str | None) -> str | None:
    """Comunidad autónoma a la que pertenece una provincia."""
    canonical = normalize_province(name)
    if canonical is None:
        return None
    for p in PROVINCES:
        if p.name == canonical:
            return p.autonomous_community
    return None


def centroid(name: str | None) -> tuple[float, float] | None:
    """Centroide (lat, lon) de una provincia por nombre."""
    canonical = normalize_province(name)
    if canonical is None:
        return None
    for p in PROVINCES:
        if p.name == canonical:
            return (p.latitude, p.longitude)
    return None


def provinces_in_community(community: str) -> list[Province]:
    """Lista de provincias de una comunidad autónoma."""
    canonical = normalize_community(community)
    return [p for p in PROVINCES if p.autonomous_community == canonical]


def community_centroid(community: str | None) -> tuple[float, float] | None:
    """Centroide (lat, lon) de una comunidad: media de sus provincias."""
    if not community:
        return None
    provs = provinces_in_community(community)
    if not provs:
        return None
    lat = sum(p.latitude for p in provs) / len(provs)
    lon = sum(p.longitude for p in provs) / len(provs)
    return (lat, lon)
