# Referencia de la API

RadarSalud expone una API REST con FastAPI bajo el prefijo `/api/v1`, además de
endpoints de salud y páginas web. Por defecto el servidor corre en
`http://127.0.0.1:8000`. La documentación interactiva está en `/docs` (Swagger) y
`/redoc`.

Arranca el servidor con `radarsalud serve` (o `make serve`).

## Salud y web

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/health` | Estado del servicio y versión. |
| GET | `/` | Página de inicio con contadores. |
| GET | `/map?mode=real\|simulation\|all` | Página del mapa. |
| GET | `/map/render?mode=...` | HTML del mapa Folium (embebible). |
| GET | `/simulation` | Página de simulación (presets y botones). |
| GET | `/sources` | Página con el catálogo de fuentes. |
| GET | `/alerts` | Página de triaje de alertas. |
| GET | `/province?name=…` | Detalle de provincia (serie observada vs. esperada). |
| GET | `/import` | Página de importación de CSV. |

## Panel, pipeline y scheduler

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/v1/dashboard/summary` | Indicadores: observaciones, alertas, última fecha, severidades. |
| GET | `/api/v1/dashboard/mortality_timeseries` | Serie nacional de mortalidad observada vs. esperada. |
| GET | `/api/v1/dashboard/top_excess?limit=10` | Provincias con mayor exceso de mortalidad. |
| GET | `/api/v1/dashboard/province_timeseries?province=…` | Serie de una provincia. |
| POST | `/api/v1/pipeline/refresh` | Lanza ingesta real + análisis en segundo plano. `{include_heavy, include_light}` |
| GET | `/api/v1/pipeline/status` | Estado del pipeline (paso, mensaje, resultado). |
| GET | `/api/v1/scheduler/status` | Estado de la actualización automática. |
| POST | `/api/v1/scheduler/start` | Activa el scheduler. `{hours, include_heavy}` |
| POST | `/api/v1/scheduler/stop` | Detiene el scheduler. |

## Exportación

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/v1/observations.csv` | Observaciones en CSV (`data_mode`, `province`, `health_event`). |
| GET | `/api/v1/alerts.csv` | Alertas en CSV (`data_mode`). |

```bash
curl http://127.0.0.1:8000/health
# {"status":"ok","service":"RadarSalud","version":"0.1.0"}
```

## Fuentes — `/api/v1/sources`

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/v1/sources` | Lista todas las fuentes. |
| POST | `/api/v1/sources` | Crea una fuente (201). |

```bash
curl http://127.0.0.1:8000/api/v1/sources

curl -X POST http://127.0.0.1:8000/api/v1/sources \
  -H "Content-Type: application/json" \
  -d '{"name":"mi_fuente","source_type":"csv","category":"salud","access_mode":"manual_download"}'
```

## Observaciones — `/api/v1/observations`

| Método | Ruta | Parámetros | Descripción |
|--------|------|------------|-------------|
| GET | `/api/v1/observations` | `data_mode`, `province`, `health_event`, `limit` (≤5000, por defecto 500) | Lista observaciones filtradas. |
| POST | `/api/v1/observations` | cuerpo JSON | Crea una observación (201). |

`data_mode` acepta `real`, `manual_import`, `simulation` o `all`.

```bash
curl "http://127.0.0.1:8000/api/v1/observations?data_mode=real&province=Madrid&limit=100"

curl -X POST http://127.0.0.1:8000/api/v1/observations \
  -H "Content-Type: application/json" \
  -d '{"observed_at":"2026-01-15T00:00:00","province":"Madrid","health_event":"gripe","signal_type":"incidencia","value":85.0,"unit":"tasa_100k"}'
```

## Carga de CSV — `/api/v1/uploads/csv`

| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/api/v1/uploads/csv` | Importa un CSV agregado como `manual_import` (multipart). |

Devuelve 422 con el detalle de errores si el CSV es rechazado (fechas inválidas,
valores no numéricos, eventos no permitidos o columnas/valores con datos
personales).

```bash
curl -X POST http://127.0.0.1:8000/api/v1/uploads/csv \
  -F "file=@datos.csv" \
  -F "source_name=mi_origen"
```

## Ingesta — `/api/v1/ingest/run`

| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/api/v1/ingest/run` | Ejecuta un conector (`{"source":"..."}`) o todos si `source` es `null`. |

Devuelve 404 si el conector indicado no existe.

```bash
# Un conector
curl -X POST http://127.0.0.1:8000/api/v1/ingest/run \
  -H "Content-Type: application/json" -d '{"source":"datos_gob_es"}'

# Todos
curl -X POST http://127.0.0.1:8000/api/v1/ingest/run \
  -H "Content-Type: application/json" -d '{}'
```

## Analítica — `/api/v1/analytics/run`

| Método | Ruta | Cuerpo | Descripción |
|--------|------|--------|-------------|
| POST | `/api/v1/analytics/run` | `data_mode`, `province`, `health_event`, `signal_type`, `start`, `end` | Detecta anomalías y crea alertas. |

`data_mode`: `real` (por defecto), `simulation` o `all`. Devuelve 422 si no es
válido.

```bash
curl -X POST http://127.0.0.1:8000/api/v1/analytics/run \
  -H "Content-Type: application/json" \
  -d '{"data_mode":"real","province":"Madrid","health_event":"gripe"}'
# {"alerts_created":3,"by_mode":{"real":{"observations":120,"alerts":3}}}
```

## Alertas — `/api/v1/alerts`

| Método | Ruta | Parámetros | Descripción |
|--------|------|------------|-------------|
| GET | `/api/v1/alerts` | `data_mode`, `province`, `health_event`, `severity`, `status`, `limit` | Lista alertas filtradas. |
| PATCH | `/api/v1/alerts/{id}/status` | `{"status":"open\|reviewed\|dismissed"}` | Cambia el estado de una alerta. |

PATCH devuelve 404 si la alerta no existe y 422 si el estado no es válido.

```bash
curl "http://127.0.0.1:8000/api/v1/alerts?data_mode=real&severity=high"

curl -X PATCH http://127.0.0.1:8000/api/v1/alerts/12/status \
  -H "Content-Type: application/json" -d '{"status":"reviewed"}'
```

## Mapas — `/api/v1/maps/alerts.geojson`

| Método | Ruta | Parámetros | Descripción |
|--------|------|------------|-------------|
| GET | `/api/v1/maps/alerts.geojson` | `mode=real\|simulation\|all` (por defecto `all`) | FeatureCollection GeoJSON de alertas. |

```bash
curl "http://127.0.0.1:8000/api/v1/maps/alerts.geojson?mode=real"
```

## Simulación — `/api/v1/simulation`

| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/api/v1/simulation/run` | Simulación a medida (cuerpo JSON). |
| POST | `/api/v1/simulation/preset/{name}` | Ejecuta un preset (404 si no existe). |
| POST | `/api/v1/simulation/clear` | Borra todas las simulaciones (no toca datos reales). |
| GET | `/api/v1/simulation/list` | Lista las simulaciones. |

Cuerpo de `/run`: `event` (`gripe|covid|vrs|gastroenteritis|golpe_calor|multi_evento`),
`province`, `autonomous_community`, `severity`, `days` (1–120), `multiplier`
(0–20), `name`, `description`.

```bash
curl -X POST http://127.0.0.1:8000/api/v1/simulation/preset/gripe_madrid

curl -X POST http://127.0.0.1:8000/api/v1/simulation/run \
  -H "Content-Type: application/json" \
  -d '{"event":"vrs","province":"Zaragoza","severity":"high","days":21,"multiplier":3.5}'

curl -X POST http://127.0.0.1:8000/api/v1/simulation/clear
curl http://127.0.0.1:8000/api/v1/simulation/list
```
