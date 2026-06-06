# Política de datos reales

RadarSalud trabaja exclusivamente con **datos abiertos y agregados**. Esta política
define cómo se obtienen, qué se permite y qué no, y cómo se documentan las fuentes
todavía no verificadas.

## Principios

1. **Priorizar fuentes oficiales y abiertas.** El orden de preferencia es:
   APIs oficiales abiertas → CSV/JSON abiertos descargables → RSS/Atom
   institucionales. Solo después se consideraría otra vía, siempre verificada.
2. **No inventar URLs.** Si una URL concreta no está verificada (existencia,
   licencia, formato estable), se deja `url: null` y estado
   `pending_verification` en `data/sources_catalog.yml`. Solo se listan dominios
   institucionales conocidos con seguridad.
3. **Respetar términos, robots.txt y límites de uso.** No se realiza scraping
   agresivo ni se eluden medidas técnicas.
4. **Cortesía de red.** El cliente HTTP (`utils/http.py`) identifica un
   `User-Agent` propio, aplica un retardo mínimo entre peticiones al mismo host
   (`RADARSALUD_HTTP_RATE_LIMIT_SECONDS`, 1 s por defecto) y un `timeout`
   (`RADARSALUD_HTTP_TIMEOUT`, 30 s).
5. **Sin datos personales.** Solo se aceptan agregados poblacionales. La
   importación CSV rechaza columnas o valores que parezcan datos personales.
6. **Sin OCR ni interpretación de informes no estructurados** en el MVP: si una
   fuente solo publica PDFs/web no estructurada, queda como plantilla documentada.

## Cómo se documentan las fuentes pendientes

Las fuentes conocidas pero no verificables se incluyen igualmente en el catálogo
con su organización, tipo y notas, pero con `access_mode: pending_verification` y
`url: null`. Sus conectores son **plantillas**: existen, están documentadas y, al
ejecutarse, devuelven `status = skipped` con un mensaje que explica qué falta para
activarlas. Así el sistema es honesto sobre lo que puede y no puede ingerir.

Para activar una fuente: verificar URL, licencia y formato; cambiar su
`access_mode` a `operative`/`open` (o `api_key_required`), rellenar la `url` e
implementar/completar el conector.

## Diferencia entre `real`, `manual_import` y `simulation`

| Modo | Origen | Cómo entra | Confianza típica |
|------|--------|-----------|------------------|
| `real` | Conectores operativos sobre fuentes abiertas. | `ingest` / `ingest-all`. | Variable, según fuente. |
| `manual_import` | CSV agregado descargado a mano por la persona usuaria. | `import-csv` / `POST /api/v1/uploads/csv`. | 0.8 (dato real cargado a mano). |
| `simulation` | Motor de simulación. | `simulate` / endpoints de simulación. | 0.5 (dato ilustrativo). |

- En analítica, `real` agrupa `real` + `manual_import` (ambos son datos reales);
  `simulation` se analiza por separado.
- Las observaciones simuladas se vinculan a un `simulation_id` y pueden borrarse
  por completo sin tocar ninguna fila real (`clear-simulations`).
- Las alertas solo se etiquetan como `real` o `simulation`.

## Trazabilidad

Cada ejecución de ingesta se registra en `ingestion_runs` (fuente, estado,
registros encontrados/insertados, mensaje de error). Cada observación guarda su
`source_id`, y cada alerta guarda los `source_ids` que la fundamentan. Así toda
señal mantiene su trazabilidad hasta la fuente abierta original.
