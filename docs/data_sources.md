# Fuentes de datos

El catálogo de fuentes vive en `data/sources_catalog.yml` y se siembra en la
tabla `sources` con `radarsalud init-db`. Cada fuente declara organización, tipo,
categoría, URL (o `null` si no está verificada), licencia y, sobre todo, su estado
de acceso (`access_mode`).

## Estados de acceso (`access_mode`)

| Estado | Significado | ¿Se ingiere automáticamente? |
|--------|-------------|------------------------------|
| `operative` / `open` | Portal o API abierta que existe y funciona. | Sí, si hay conector operativo. |
| `api_key_required` | Requiere clave configurada en `.env`. | Solo con la clave; si falta, desactivado. |
| `manual_download` | Hay datos abiertos pero se descargan/cargan a mano (CSV). | No; vía `import-csv`. |
| `pending_verification` | Fuente conocida con URL/licencia/formato sin verificar. | No. |

> **Regla de oro:** no se inventan URLs. Si una URL concreta no está verificada,
> se deja `url: null` y estado `pending_verification`. Solo se listan dominios
> institucionales reales conocidos con seguridad.

Al sembrar, `operative`/`open` quedan `enabled = true`; el resto, `enabled = false`.

## Fuentes nacionales

| Fuente | Organización | Tipo | Estado | Conector | Notas |
|--------|--------------|------|--------|----------|-------|
| `datos_gob_es` | datos.gob.es (Gobierno de España) | api | **operative** | `datos_gob_es` (operativo) | API abierta del catálogo nacional, sin clave. Descubre datasets de salud pública y guarda metadatos (enlaces), no valores. |
| `isciii_momo` | ISCIII - MoMo | csv | **operative** | `isciii_momo` (operativo, **pesado**) | **Mortalidad observada y esperada por provincia y fecha** (CSV abierto). Es la fuente que llena el mapa con datos reales. Volcado ~700 MB en streaming; excluido de `ingest-all` salvo `--include-heavy`. Ejecutar: `radarsalud ingest --source isciii_momo`. |
| `ine_poblacion` | INE | api | manual_download | `ine` (plantilla) | Población por provincia/municipio para tasas. API Tempus3 / CSV; endpoint por fijar. |
| `aemet_opendata` | AEMET | api | api_key_required | `aemet` (plantilla) | Temperatura, avisos, calor extremo. Requiere `AEMET_API_KEY`. Sin clave, desactivado. |
| `isciii_sivira` | ISCIII - SiVIRA | html | pending_verification | `isciii_sivira` (plantilla) | Gripe, COVID-19, VRS. Mucha info en informes; sin OCR en el MVP. |
| `ministerio_sanidad` | Ministerio de Sanidad | html | pending_verification | `ministerio_sanidad` (plantilla) | Boletines/datos. Pendiente de recursos estructurados estables. |
| `calidad_aire_nacional` | MITECO / CCAA | api | pending_verification | `calidad_aire` (plantilla) | Índices por estación/provincia. `url: null`. |
| `aguas_residuales` | Programas de vigilancia (SARS-CoV-2) | csv | pending_verification | `aguas_residuales` (plantilla) | Carga viral como señal temprana. `url: null`. |
| `boe_datos_abiertos` | BOE | api | pending_verification | `boe` (plantilla) | Avisos oficiales como señal contextual, no indicador directo. |
| `rss_institucional` | Organismos públicos (varios) | rss | pending_verification | `rss_institucional` (operativo) | Lee feeds RSS marcados como operativos en el catálogo; ninguno verificado por defecto. |

## Fuentes por comunidad autónoma

Portales de datos abiertos cuyo dominio se conoce con seguridad se marcan como
`manual_download` (la ingesta automática de sus datasets concretos es trabajo
futuro). Donde no hay certeza de URL, `pending_verification` + `url: null`.

| CCAA | Fuente | URL | Estado |
|------|--------|-----|--------|
| Andalucía | `andalucia_datos_abiertos` | juntadeandalucia.es/datosabiertos | manual_download |
| Aragón | `aragon_opendata` | opendata.aragon.es | manual_download |
| Asturias | `asturias_salud` | — | pending_verification |
| Baleares | `baleares_salud` | — | pending_verification |
| Canarias | `canarias_datos` | datos.canarias.es | manual_download |
| Cantabria | `cantabria_salud` | — | pending_verification |
| Castilla-La Mancha | `clm_salud` | — | pending_verification |
| Castilla y León | `cyl_datos_abiertos` | datosabiertos.jcyl.es | manual_download |
| Cataluña | `cataluna_analisi` | analisi.transparenciacatalunya.cat | manual_download |
| Com. Valenciana | `gva_dades_obertes` | dadesobertes.gva.es | manual_download |
| Extremadura | `extremadura_salud` | — | pending_verification |
| Galicia | `galicia_abertos` | abertos.xunta.gal | manual_download |
| Madrid | `madrid_datos` | datos.comunidad.madrid | manual_download |
| Murcia | `murcia_salud` | — | pending_verification |
| Navarra | `navarra_gobierno_abierto` | gobiernoabierto.navarra.es | manual_download |
| País Vasco | `euskadi_opendata` | opendata.euskadi.eus | manual_download |
| La Rioja | `rioja_salud` | — | pending_verification |
| Ceuta | `ceuta_salud` | — | pending_verification |
| Melilla | `melilla_salud` | — | pending_verification |

## Conectores: operativos vs. plantillas

Cada conector declara `name`, `operational` y un método `fetch()`.

**Operativos** (ejecutan ingesta real ahora mismo):

- `datos_gob_es` — consulta la API abierta `datos.gob.es/es/apidata` sin clave,
  busca términos de interés (gripe, covid, aguas residuales, calidad del aire,
  temperatura, mortalidad, urgencias...) y **guarda metadatos** de datasets
  descubiertos (no asume que todos sean descargables). Degrada con elegancia si
  no hay red (`failed`).
- `rss_institucional` — lee feeds RSS/Atom de organismos públicos marcados como
  operativos en el catálogo (con `feedparser`). Como **ninguno está verificado
  por defecto**, se salta documentando el motivo; no usa prensa generalista.

**Plantillas documentadas** (`status = skipped`, desactivadas hasta verificar):

- `ine_poblacion`, `isciii_sivira`, `ministerio_sanidad`, `calidad_aire_nacional`,
  `aguas_residuales`, `boe_datos_abiertos`, `comunidades_autonomas`.
- `aemet_opendata` — operativo solo si existe `AEMET_API_KEY`; la implementación
  de endpoints concretos (avisos CAP, climatología) queda documentada como
  plantilla.
- `csv_local` — no participa en `ingest-all` (necesita un fichero); gestiona la
  importación manual de CSV agregado.

Aunque una plantilla no inserte datos, `ingest-all` registra su intento como
`ingestion_run` con estado `skipped` para mantener la trazabilidad.
