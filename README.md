# 🛰️ RadarSalud

**Plataforma local y open source de vigilancia epidemiológica** basada en
**fuentes abiertas reales** y con un **modo simulación** separado para pruebas y
docencia. Mapa interactivo de España, detección de anomalías y API + CLI.

> RadarSalud es una herramienta de **vigilancia poblacional** sobre señales
> abiertas **agregadas**. **No usa datos personales. No diagnostica. No
> sustituye a profesionales sanitarios.** Toda alerta requiere validación por
> salud pública.

Pensada para **ayuntamientos, centros de salud, analistas de salud pública,
investigadores y docencia**.

---

## ✨ Características

- 🗄️ **SQLite + SQLAlchemy** — base local, sin servidores ni Docker.
- 🌐 **Datos reales de fuentes abiertas** — conector operativo de `datos.gob.es`,
  RSS institucionales, plantillas documentadas (INE, AEMET, ISCIII/SiVIRA,
  Ministerio de Sanidad, calidad del aire, aguas residuales, BOE) y catálogo por
  comunidad autónoma. **Sin URLs inventadas.**
- 📥 **Importación de CSV real agregado** con validación (fechas, provincias,
  valores, eventos permitidos y **rechazo de datos personales**).
- 🧪 **Modo simulación** activable desde un **botón**, API y CLI, totalmente
  **separado de los datos reales** y **limpiable**.
- 📈 **Detección de anomalías** — media móvil, z-score, z-score robusto
  (mediana/MAD), baseline histórico y subida porcentual.
- 🗺️ **Mapa interactivo de España** (Folium) con capas por evento y por modo,
  color por severidad y marcado claro de la simulación.
- ⚡ **API FastAPI** (`/docs`) y **CLI Typer**.

## 🔑 Los tres modos de dato

| `data_mode`     | Origen                                   | Mezcla |
|-----------------|------------------------------------------|--------|
| `real`          | Ingesta de fuentes abiertas              | nunca con simulación |
| `manual_import` | CSV agregado descargado manualmente      | tratado como real en análisis |
| `simulation`    | Motor de simulación (pruebas/docencia)   | aislado y borrable |

## 🚀 Instalación rápida (sin Docker)

### 🪟 Windows — todo en uno (recomendado)

Haz **doble clic** en **`RadarSalud.bat`** (o ejecútalo desde `cmd`). El script,
de forma automática: detecta Python, crea el entorno virtual, instala las
dependencias, crea la base SQLite, ingiere datos reales abiertos, detecta
anomalías, **abre el navegador** y arranca el servidor. Requisito previo:
[Python 3.11+](https://www.python.org/downloads/) con *“Add Python to PATH”*.

Para detener el servidor: `Ctrl+C` en la ventana o ciérrala.

### 🐧 Linux / macOS

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

radarsalud init-db        # crea SQLite + siembra el catálogo de fuentes
radarsalud ingest-all     # ingesta de fuentes ligeras (catálogo, RSS…)
radarsalud ingest --source isciii_momo   # DATOS REALES: mortalidad por provincia (ISCIII MoMo)
radarsalud analyze --mode real           # detecta anomalías sobre los datos reales
radarsalud serve          # arranca FastAPI en http://127.0.0.1:8000
```

> **¿De dónde salen los datos del mapa?** El conector **ISCIII MoMo** descarga
> mortalidad diaria **real, observada y esperada, por provincia** (CSV abierto).
> Tras `ingest --source isciii_momo` + `analyze`, el mapa muestra el último valor
> por provincia (color según exceso sobre lo esperado) y las anomalías
> detectadas. Es una descarga grande (~700 MB en streaming, ~30–90 s), por eso es
> un conector «pesado» y no entra en `ingest-all` por defecto.

Después abre:

- API / Swagger: <http://127.0.0.1:8000/docs>
- Panel: <http://127.0.0.1:8000/>
- Mapa: <http://127.0.0.1:8000/map>
- Simulación: <http://127.0.0.1:8000/simulation>

> Con `make` disponible: `make dev && make init-db && make serve`.

## 🧪 Probar el modo simulación

Desde la web en `/simulation` (botones **Lanzar simulación** y **Limpiar
simulaciones**), o por CLI:

```bash
radarsalud simulate --preset gripe_madrid
radarsalud simulate --event gripe --province Madrid --severity high --days 14 --multiplier 2.5
radarsalud map --mode simulation
radarsalud clear-simulations     # no toca los datos reales
```

Presets: `gripe_madrid`, `covid_barcelona`, `gastro_valencia`, `calor_sevilla`,
`vrs_zaragoza`, `multi_evento`.

## 📥 Importar un CSV real agregado

Columnas aceptadas: `observed_at, autonomous_community, province, municipality,
signal_type, health_event, pathogen, value, unit, source_name`.

```bash
radarsalud import-csv mis_datos.csv --mode manual_import
```

Se validan fechas, provincias, valores numéricos y eventos permitidos, y se
**rechaza** cualquier columna o contenido con aspecto de dato personal.

## 🧰 Comandos CLI

`init-db`, `sources-list`, `ingest --source NOMBRE`, `ingest-all`,
`import-csv FICHERO --mode`, `analyze --mode real|simulation|all`,
`simulate --preset ... | --event ...`, `clear-simulations`,
`map --mode real|simulation|all`, `serve`.

## 🧪 Tests y lint

```bash
pytest          # batería de tests
ruff check .    # linter
```

## 📚 Documentación

En [`docs/`](docs/): arquitectura, fuentes de datos, política de datos reales,
modo simulación, privacidad y ética, casos de uso de salud pública, API, mapas e
instalación local. Hoja de ruta en [`ROADMAP.md`](ROADMAP.md).

## 🔐 Configuración (`.env`)

Copia `.env.example` a `.env`. Ninguna clave es obligatoria para arrancar. El
conector AEMET se activa si defines `AEMET_API_KEY` (clave gratuita de
[AEMET OpenData](https://opendata.aemet.es/)); sin ella queda desactivado y
documentado.

## ⚖️ Licencia

[MIT](LICENSE). Las licencias de los **datos** dependen de cada fuente original;
consulta el catálogo de fuentes y `docs/real_data_policy.md`.
