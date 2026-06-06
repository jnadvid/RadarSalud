# Arquitectura de RadarSalud

RadarSalud es una plataforma **local y open source** de vigilancia epidemiológica
poblacional basada en **señales abiertas y agregadas**. No usa datos personales,
no diagnostica y no sustituye a profesionales sanitarios.

## Pila tecnológica

| Capa | Tecnología |
|------|------------|
| Lenguaje | Python 3.11+ |
| Base de datos | SQLite + SQLAlchemy 2.0 (ORM tipado) |
| API y web | FastAPI + uvicorn, plantillas Jinja2 |
| Análisis de datos | Pandas |
| Red / scraping | httpx, requests, BeautifulSoup4, feedparser |
| Mapas | Folium |
| CLI | Typer |
| Tests | Pytest |
| Configuración | pydantic-settings + `.env` |

No hay Docker, ni PostgreSQL/PostGIS. Todo corre en local con un único fichero
SQLite.

## Los tres modos de dato

El sistema distingue siempre el `data_mode` de cada observación/alerta y **nunca
los mezcla**:

- `real` — ingerido de fuentes abiertas operativas por los conectores.
- `manual_import` — CSV agregado descargado y cargado a mano por la persona usuaria.
- `simulation` — generado por el motor de simulación para pruebas y docencia.

> **Principio rector:** los datos reales y los simulados nunca se mezclan ni se
> contaminan. El modo simulación es totalmente separable, marcable y borrable
> (cada lote se vincula a un `simulation_id`).

En analítica, el modo `real` agrupa `real` + `manual_import`; el modo `simulation`
se analiza por separado; el modo `all` ejecuta ambos por separado, nunca juntos.

## Capas y flujo de datos

```
config ──► database ──► models
                          ▲
   connectors ─► normalizers ─► services ─► analytics
   (fuentes)                       │           │
   simulation ─────────────────────┤           ▼
                                   ├──► maps (Folium / GeoJSON)
                                   ▼
                              api (FastAPI) ──► web (Jinja2)
                                   ▲
                                  cli (Typer)
```

- **config** (`config.py`): `Settings` con valores por defecto seguros, leídos de
  `.env` (BD, host/puerto, AEMET key, rate-limit HTTP, logging).
- **database** (`database.py`): `Base` declarativa, motor SQLite, `session_scope`
  y `get_session`, `init_db()`.
- **models**: tablas ORM (ver más abajo).
- **connectors**: un conector por fuente; los operativos hacen `fetch()` real, el
  resto son plantillas documentadas (`status = skipped`).
- **normalizers**: fechas, geografía (provincias/CCAA/centroides), señales y
  unidades.
- **analytics**: detección de anomalías (baseline, z-score, z-score robusto,
  subida porcentual, media móvil), severidad y explicaciones.
- **simulation**: presets, escenarios y motor generador de series de brote.
- **maps**: GeoJSON de España, capas, colores y render Folium.
- **services**: orquestación (ingesta, analítica, simulación, mapa, alertas).
- **api**: routers FastAPI REST (`/api/v1/...`) + endpoints de salud y web.
- **web**: páginas Jinja2 (`/`, `/map`, `/simulation`, `/sources`).
- **cli**: comandos Typer (`radarsalud ...`).

### Flujo típico

1. `init-db` crea la base y siembra el catálogo (`sources_catalog.yml`).
2. `ingest-all` ejecuta los conectores; los operativos insertan observaciones
   `real`; los demás registran un `ingestion_run` `skipped` por trazabilidad.
3. `import-csv` valida y carga observaciones `manual_import`.
4. `analyze` detecta anomalías y persiste alertas por modo.
5. `simulate` crea un lote `simulation` separado.
6. `map` / `/map` renderiza el mapa Folium con las alertas.

## Tablas de la base de datos

| Tabla | Modelo | Contenido |
|-------|--------|-----------|
| `sources` | `Source` | Catálogo de fuentes (tipo, categoría, URL, estado `access_mode`). |
| `observations` | `Observation` | Señales agregadas (`data_mode`, territorio, evento, valor). |
| `alerts` | `Alert` | Anomalías detectadas (severidad, baseline, explicación, estado). |
| `simulations` | `Simulation` | Lotes de simulación con escenario y parámetros. |
| `ingestion_runs` | `IngestionRun` | Trazabilidad de cada intento de ingesta. |
| `geo_units` | `GeoUnit` | 50 provincias + Ceuta y Melilla con centroides. |

Las observaciones simuladas llevan `data_mode = simulation` y `simulation_id`; las
alertas solo se etiquetan como `real` o `simulation` (nunca `manual_import`).

## Estructura de directorios

```
RadarSalud/
├── data/
│   └── sources_catalog.yml      # catálogo de fuentes
├── docs/                        # esta documentación
├── radarsalud/
│   ├── config.py  database.py  main.py  cli.py
│   ├── models/        # source, observation, alert, simulation, ingestion_run, geo
│   ├── schemas/       # esquemas Pydantic de la API
│   ├── connectors/    # datos_gob, rss, aemet, ine, csv_local, plantillas...
│   ├── normalizers/   # dates, geography, signals, units
│   ├── analytics/     # anomalies, baseline, severity, explanations
│   ├── simulation/    # presets, scenarios, engine
│   ├── maps/          # spain_geojson, layers, folium_map
│   ├── services/      # ingestion, analytics, simulation, map, alert
│   ├── api/           # routes_* (sources, observations, alerts, maps, ...)
│   ├── web/           # templates Jinja2 + estáticos
│   └── utils/         # http, logging, validation
├── tests/             # database, connectors, anomalies, simulation, api, map
├── pyproject.toml  Makefile  .env.example
```
