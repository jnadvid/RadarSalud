# ROADMAP — RadarSalud

RadarSalud es una plataforma **local y open source** de vigilancia epidemiológica
poblacional basada en **señales abiertas y agregadas**. No usa datos personales,
no diagnostica y no sustituye a profesionales sanitarios.

El sistema distingue siempre tres tipos de dato (`data_mode`):

- `real` — ingerido de fuentes abiertas operativas.
- `manual_import` — CSV agregado descargado manualmente por la persona usuaria.
- `simulation` — generado por el motor de simulación para pruebas y docencia.

## Principio rector

> Los datos reales y los simulados **nunca se mezclan ni se contaminan**. El modo
> simulación es totalmente separable, marcable y borrable.

---

## Fase 0 — Andamiaje (hecho)

- [x] Estructura del repositorio.
- [x] `pyproject.toml`, `Makefile`, `.env.example`, `LICENSE`.
- [x] `ROADMAP.md` y documentación de arquitectura.

## Fase 1 — Núcleo de datos (prioridad 1)

- [x] Configuración (`config.py`) con `.env`.
- [x] Capa de base de datos SQLite + SQLAlchemy (`database.py`).
- [x] Modelos: `sources`, `observations`, `alerts`, `simulations`, `ingestion_runs`, `geo`.
- [x] `data_mode` presente en observaciones y alertas.
- [x] `radarsalud init-db` crea la base y siembra el catálogo.

## Fase 2 — Catálogo de fuentes reales (prioridad 2)

- [x] `data/sources_catalog.yml` con fuentes nacionales y por comunidad autónoma.
- [x] Estados: `operative`, `api_key_required`, `manual_download`, `pending_verification`.
- [x] Siembra del catálogo en la tabla `sources`.
- [x] Sin URLs inventadas: lo no verificado queda como `pending_verification`.

## Fase 3 — Importación CSV real agregada (prioridad 3)

- [x] `POST /api/v1/uploads/csv` y `radarsalud import-csv`.
- [x] Validación de fechas, provincias, valores numéricos y eventos permitidos.
- [x] Comprobación de ausencia de columnas con datos personales.
- [x] Marcado como `data_mode = manual_import`.

## Fase 4 — Mapa de España (prioridad 4)

- [x] GeoJSON de provincias y centroides (`maps/spain_geojson.py`).
- [x] Mapa Folium con capas por evento y por modo.
- [x] `/map` y `/api/v1/maps/alerts.geojson?mode=real|simulation|all`.
- [x] `radarsalud map --mode ...`.

## Fase 5 — Modo simulación desde botón (prioridad 5)

- [x] Motor de simulación (`simulation/engine.py`) + escenarios y presets.
- [x] Página `/simulation` con botones *Lanzar* y *Limpiar*.
- [x] Endpoints `POST /api/v1/simulation/run|preset|clear` y `GET /list`.
- [x] Observaciones y alertas marcadas como `SIMULACIÓN`.

## Fase 6 — API y CLI (prioridad 6)

- [x] API FastAPI completa (sources, observations, alerts, maps, analytics, ingestion, simulation).
- [x] CLI Typer completa.

## Fase 7 — Detección de anomalías (prioridad 7)

- [x] Media móvil, z-score, z-score robusto (mediana/MAD), baseline histórico, subida %.
- [x] Filtro por `data_mode`, provincia, evento, señal y rango temporal.
- [x] Generación de alertas con severidad y explicación.

## Fase 8 — Conectores reales verificables (prioridad 8)

- [x] `datos.gob.es` (API abierta de catálogo).
- [x] RSS institucionales (feedparser).
- [x] INE, AEMET, ISCIII/SiVIRA, Ministerio de Sanidad, calidad del aire,
      aguas residuales: conectores con plantilla documentada y estado real.
- [x] Conectores que requieren clave/descarga manual: desactivados pero documentados.

## Fase 9 — Documentación y tests (prioridad 9)

- [x] `docs/` completo (arquitectura, fuentes, política de datos reales, ética…).
- [x] Tests: base de datos, conectores, anomalías, simulación, API, mapa.

---

## Trabajo futuro (post-MVP)

- Programación de ingestas con APScheduler (opcional ya incluido como dependencia extra).
- Más conectores autonómicos a medida que se verifiquen URLs y licencias.
- Normalización fina por municipio con códigos INE completos.
- Tasas por 100.000 habitantes usando población del INE en todas las señales.
- Exportación de informes PDF/HTML para salud pública.
- Validación participativa de alertas (workflow de revisión).
