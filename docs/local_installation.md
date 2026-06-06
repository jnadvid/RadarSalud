# Instalación local (sin Docker)

RadarSalud se ejecuta en local sobre Python 3.11+ y SQLite. **No requiere Docker
ni PostgreSQL/PostGIS.** Ninguna clave es obligatoria para arrancar el MVP.

## Requisitos

- Python 3.11 o superior.
- `pip` y `venv`.
- (Opcional) `make` para usar los atajos del Makefile.

## Instalación con entorno virtual

```bash
# 1. Crear y activar el entorno virtual
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 2. Instalar el paquete en modo editable con dependencias de desarrollo
pip install --upgrade pip
pip install -e ".[dev]"
```

`".[dev]"` añade pytest, pytest-cov, httpx y ruff. Para una instalación mínima sin
herramientas de desarrollo, usa `pip install -e .`. El extra opcional `scheduler`
(`pip install -e ".[scheduler]"`) añade APScheduler para programar ingestas
(trabajo futuro).

La instalación registra el comando `radarsalud`.

## Configuración (`.env`)

Copia `.env.example` a `.env` y ajústalo si lo necesitas (todos los valores tienen
un defecto seguro):

```bash
cp .env.example .env
```

Variables principales:

| Variable | Defecto | Uso |
|----------|---------|-----|
| `RADARSALUD_DATABASE_URL` | `sqlite:///data/radarsalud.sqlite` | Base de datos. |
| `RADARSALUD_HOST` | `127.0.0.1` | Host del servidor. |
| `RADARSALUD_PORT` | `8000` | Puerto del servidor. |
| `RADARSALUD_DEBUG` | `false` | Modo depuración. |
| `AEMET_API_KEY` | (vacío) | Activa el conector AEMET. Si falta, queda desactivado. |
| `DATOS_GOB_BASE_URL` | `https://datos.gob.es/apidata` | Base de la API de datos.gob.es. |
| `RADARSALUD_HTTP_TIMEOUT` | `30` | Timeout HTTP (s). |
| `RADARSALUD_HTTP_RATE_LIMIT_SECONDS` | `1.0` | Cortesía entre peticiones al mismo host. |
| `RADARSALUD_USER_AGENT` | (identificable) | User-Agent de las peticiones. |
| `RADARSALUD_LOG_LEVEL` | `INFO` | Nivel de log. |

## Primeros pasos

```bash
# 1. Crear la base SQLite y sembrar el catálogo de fuentes
radarsalud init-db

# 2. Ejecutar la ingesta de fuentes reales (operativas + plantillas)
radarsalud ingest-all

# 3. Detectar anomalías sobre datos reales y crear alertas
radarsalud analyze --mode real

# 4. (Opcional) Lanzar una simulación de demostración
radarsalud simulate --preset gripe_madrid

# 5. Generar el mapa como HTML
radarsalud map --mode all

# 6. Arrancar el servidor web + API
radarsalud serve
```

Con el servidor en marcha, abre en el navegador:

- `http://127.0.0.1:8000/` — inicio con contadores.
- `http://127.0.0.1:8000/map` — mapa de España.
- `http://127.0.0.1:8000/simulation` — lanzar/limpiar simulaciones.
- `http://127.0.0.1:8000/sources` — catálogo de fuentes.
- `http://127.0.0.1:8000/docs` — documentación interactiva de la API.

## Atajos del Makefile

| Comando | Acción |
|---------|--------|
| `make install` | Crea el venv e instala el paquete (editable). |
| `make dev` | Instala con dependencias de desarrollo. |
| `make init-db` | Crea la base SQLite y siembra el catálogo. |
| `make ingest` | Ejecuta `radarsalud ingest-all`. |
| `make analyze` | Detecta anomalías sobre datos reales. |
| `make simulate` | Lanza el preset `gripe_madrid`. |
| `make clear-sim` | Limpia todas las simulaciones. |
| `make map` | Genera el mapa (modo `all`) en `data/processed/`. |
| `make serve` | Arranca el servidor FastAPI local. |
| `make test` | Ejecuta la batería de tests con pytest. |
| `make lint` | Ejecuta ruff. |
| `make clean` | Borra artefactos generados (no toca `.env`). |

## Tests

```bash
make test        # o: pytest
```

Los tests cubren base de datos, conectores, anomalías, simulación, API y mapa.
