# Modo simulación

El modo simulación genera datos de brote **sintéticos** para pruebas, demos y
docencia, sin tocar jamás los datos reales. Todo lo que produce se marca como
`SIMULACIÓN` y puede borrarse por completo.

## Garantía de separación

Cada ejecución crea un registro en `simulations` y genera:

- Observaciones con `data_mode = simulation` y `simulation_id` del lote.
- Alertas con `data_mode = simulation`, detectadas **solo** sobre las
  observaciones de esa simulación.

Los datos simulados **nunca** se mezclan con los reales: la analítica los procesa
por separado y la limpieza los elimina sin afectar a ninguna fila real.

## Cómo se ejecuta una simulación

### Desde la interfaz web

En `/simulation` hay botones **Lanzar** (por preset) y **Limpiar**. La página
lista los presets disponibles y las últimas simulaciones ejecutadas.

### Desde la API

```bash
# Preset
curl -X POST http://127.0.0.1:8000/api/v1/simulation/preset/gripe_madrid

# Personalizada
curl -X POST http://127.0.0.1:8000/api/v1/simulation/run \
  -H "Content-Type: application/json" \
  -d '{"event":"covid","province":"Barcelona","severity":"high","days":18,"multiplier":2.5}'

# Limpiar todas las simulaciones
curl -X POST http://127.0.0.1:8000/api/v1/simulation/clear

# Listar simulaciones
curl http://127.0.0.1:8000/api/v1/simulation/list
```

### Desde la CLI

```bash
radarsalud simulate --preset gripe_madrid
radarsalud simulate --event covid --province Barcelona --severity high --days 18 --multiplier 2.5
radarsalud clear-simulations
```

## Presets disponibles

| Preset | Evento | Provincia / CCAA | Severidad | Días | Multiplicador |
|--------|--------|------------------|-----------|------|---------------|
| `gripe_madrid` | gripe | Madrid | high | 21 | 3.0 |
| `covid_barcelona` | covid | Barcelona / Cataluña | medium | 18 | 2.5 |
| `gastro_valencia` | gastroenteritis | Valencia / C. Valenciana | medium | 10 | 2.8 |
| `calor_sevilla` | golpe_calor | Sevilla / Andalucía | high | 7 | 4.0 |
| `vrs_zaragoza` | vrs | Zaragoza / Aragón | high | 21 | 3.5 |
| `multi_evento` | multi_evento | varias provincias | high | 14 | 3.0 |

## Parámetros del escenario

`run_simulation` acepta:

- `event` — tipo de escenario: `gripe`, `covid`, `vrs`, `gastroenteritis`,
  `golpe_calor` o `multi_evento` (cualquier otro valor cae a `gripe`).
- `province` / `autonomous_community` — localización. Con provincia se genera una
  serie; con comunidad, una serie por cada provincia de la comunidad; sin ninguna,
  se usa Madrid por defecto.
- `severity` — `low | medium | high | critical` (factor 1.0 / 1.6 / 2.4 / 3.2).
- `days` — días de la serie (por defecto 14).
- `multiplier` — intensidad adicional del pico (por defecto 2.0–2.5).

Cada escenario define un perfil (señal, unidad, patógeno, línea base y
multiplicador de pico). Por ejemplo: gripe → `incidencia` en `tasa_100k` con base
40 (Influenza A/B); covid → `positividad` en `%` (SARS-CoV-2); vrs → `ingresos` en
`casos`; gastroenteritis → `urgencias` (Norovirus); golpe_calor → `urgencias`.

El motor (`simulation/engine.py`) produce una **curva de brote** (campana
gaussiana asimétrica con pico en torno al 70 % del periodo) con ruido controlado,
coordenadas por centroide provincial y `confidence_score = 0.5`.

`multi_evento` combina gripe (Madrid), covid (Barcelona), vrs (Zaragoza),
gastroenteritis (Valencia) y golpe_calor (Sevilla) en una sola ejecución.

## Marcado y limpieza

- En el mapa, las simulaciones se dibujan con **borde morado discontinuo**,
  etiqueta `[SIM]` en el tooltip y badge `SIMULACIÓN` en el popup.
- El registro de simulación guarda la nota: *"Datos simulados. No representan una
  situación sanitaria real."*
- `clear-simulations` (o `POST /api/v1/simulation/clear`) borra todas las
  observaciones y alertas con `data_mode = simulation` y marca las simulaciones
  como `cleared`. **No toca ni una fila real.**
