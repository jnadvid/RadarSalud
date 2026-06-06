"""Validaciones transversales: eventos permitidos, ausencia de datos personales."""
from __future__ import annotations

import re

# Eventos sanitarios permitidos en señales agregadas.
ALLOWED_HEALTH_EVENTS: set[str] = {
    "gripe",
    "covid",
    "vrs",
    "gastroenteritis",
    "golpe_calor",
    "calidad_aire",
    "calor_extremo",
    "infeccion_respiratoria_aguda",
    "mortalidad",
    "urgencias",
    "otro",
    "multi_evento",
}

# Tipos de señal permitidos.
ALLOWED_SIGNAL_TYPES: set[str] = {
    "incidencia",
    "casos",
    "positividad",
    "ingresos",
    "urgencias",
    "temperatura",
    "aviso_meteo",
    "carga_viral_aguas",
    "indice_calidad_aire",
    "rss_signal",
    "institutional_notice",
    "mortalidad",
    "otro",
}

# Columnas o términos prohibidos por riesgo de dato personal.
FORBIDDEN_PERSONAL_FIELDS: set[str] = {
    "nombre",
    "apellido",
    "apellidos",
    "name",
    "surname",
    "dni",
    "nif",
    "nie",
    "pasaporte",
    "passport",
    "telefono",
    "phone",
    "movil",
    "email",
    "correo",
    "direccion",
    "address",
    "domicilio",
    "cip",
    "ssn",
    "numero_seguridad_social",
    "historia_clinica",
    "patient",
    "paciente",
    "fecha_nacimiento",
    "birthdate",
    "iban",
    "tarjeta_sanitaria",
}

_DNI_RE = re.compile(r"\b\d{8}[A-Za-z]\b")
_EMAIL_RE = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")
_PHONE_RE = re.compile(r"\b(?:\+?34)?[\s-]?[6789]\d{2}[\s-]?\d{3}[\s-]?\d{3}\b")


def check_no_personal_columns(columns: list[str]) -> list[str]:
    """Devuelve la lista de columnas prohibidas encontradas (vacía si todo OK)."""
    found = []
    for col in columns:
        normalized = re.sub(r"[^a-z0-9]", "_", col.strip().lower())
        if normalized in FORBIDDEN_PERSONAL_FIELDS:
            found.append(col)
    return found


def looks_like_personal_data(value: str) -> bool:
    """Heurística para detectar posibles datos personales en texto libre."""
    if not isinstance(value, str):
        return False
    return bool(_DNI_RE.search(value) or _EMAIL_RE.search(value) or _PHONE_RE.search(value))


def is_allowed_event(event: str | None) -> bool:
    return event is None or event in ALLOWED_HEALTH_EVENTS


def is_allowed_signal(signal: str | None) -> bool:
    return signal is None or signal in ALLOWED_SIGNAL_TYPES
