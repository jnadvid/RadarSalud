"""Modelos ORM de RadarSalud. Importar este paquete registra todas las tablas."""
from radarsalud.models.alert import Alert
from radarsalud.models.geo import GeoUnit
from radarsalud.models.ingestion_run import IngestionRun
from radarsalud.models.observation import Observation
from radarsalud.models.simulation import Simulation
from radarsalud.models.source import Source

__all__ = [
    "Alert",
    "GeoUnit",
    "IngestionRun",
    "Observation",
    "Simulation",
    "Source",
]

# Constantes de dominio reutilizadas por modelos, esquemas y servicios.
DATA_MODES = ("real", "manual_import", "simulation")
SEVERITIES = ("low", "medium", "high", "critical")
ALERT_STATUSES = ("open", "reviewed", "dismissed")
SIMULATION_STATUSES = ("created", "running", "completed", "failed", "cleared")
SOURCE_TYPES = ("api", "csv", "rss", "html", "manual")
SOURCE_CATEGORIES = (
    "salud",
    "meteorologia",
    "aguas_residuales",
    "calidad_aire",
    "poblacion",
    "boletin",
    "rss",
    "otro",
)
ACCESS_MODES = ("open", "api_key_required", "manual_download", "pending_verification")
SCENARIO_TYPES = ("gripe", "covid", "vrs", "gastroenteritis", "golpe_calor", "multi_evento")
