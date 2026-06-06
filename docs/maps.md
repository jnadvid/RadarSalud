# Mapa de España

RadarSalud representa las alertas sobre un mapa interactivo de España generado con
**Folium**. El mapa se centra en `(40.0, -3.7)` con zoom 6, base
`cartodbpositron`, y usa **marcadores en el centroide de cada provincia** (en el
MVP no se dibujan polígonos, para mantener el repositorio ligero).

## Cómo verlo

- **Web:** `http://127.0.0.1:8000/map?mode=all` (la página incrusta
  `/map/render`). `mode` admite `real`, `simulation` o `all`.
- **CLI:** genera un HTML autónomo.

```bash
radarsalud map --mode all
radarsalud map --mode real --output mi_mapa.html
```

Sin `--output`, el HTML se guarda en `data/processed/mapa_<modo>.html`.

## Capas

El control de capas (no plegado) permite encender/apagar grupos. Hay **dos tipos
de capas**:

- **Por modo:** *Datos reales* y *Simulación* (visibles por defecto).
- **Por evento** (temáticas, ocultas por defecto): Gripe, COVID-19, VRS,
  Gastroenteritis, Golpe de calor, Calor extremo, Calidad del aire. Cada alerta se
  añade tanto a su capa de modo como a su capa temática.

## Colores por severidad

| Severidad | Color | Hex |
|-----------|-------|-----|
| low (baja) | verde | `#2ecc71` |
| medium (media) | amarillo | `#f1c40f` |
| high (alta) | naranja | `#e67e22` |
| critical (crítica) | rojo | `#e74c3c` |
| (desconocida) | azul | `#3498db` |

El relleno del marcador (`CircleMarker`) toma el color de la severidad. Una leyenda
fija en la esquina inferior izquierda resume esta escala.

## Marcado de simulaciones

Las alertas simuladas se distinguen visualmente con claridad:

- **Borde morado discontinuo** (`#8e44ad`, `dash_array="5,5"`, mayor grosor y
  radio) frente al borde sólido de los datos reales.
- **Etiqueta `[SIM]`** en el tooltip.
- **Badge `SIMULACIÓN`** (morado) en el popup; los datos reales muestran `REAL`
  (verde).

## Campos del popup

Al pulsar un marcador, el popup muestra:

- **Modo** (badge REAL / SIMULACIÓN)
- **Evento** (health_event)
- **Provincia**
- **Fecha** (observed_at)
- **Severidad**
- **Valor observado**
- **Baseline** (valor de referencia)
- **Explicación** (método disparado y descripción)
- **Fuente** (nombres de las fuentes que fundamentan la alerta, o `—`)
- **Recomendación**

## Endpoint GeoJSON

Para integraciones, el mapa de alertas también se sirve como GeoJSON:

```
GET /api/v1/maps/alerts.geojson?mode=real|simulation|all
```

Devuelve un `FeatureCollection` de puntos (`[longitud, latitud]`) cuyas
`properties` incluyen `data_mode`, `health_event`, `province`,
`autonomous_community`, `observed_at`, `severity`, `observed_value`,
`baseline_value`, `explanation`, `recommendation` y `source`.

```bash
curl "http://127.0.0.1:8000/api/v1/maps/alerts.geojson?mode=all"
```

Las coordenadas se resuelven desde la alerta; si no las tiene, se usa el centroide
provincial (tabla `geo_units` / normalizador de geografía). Las alertas sin
coordenadas resolubles se omiten del mapa.
