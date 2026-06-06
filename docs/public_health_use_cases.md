# Casos de uso en salud pública

RadarSalud agrega señales abiertas y detecta anomalías para apoyar la vigilancia
poblacional. A continuación, ejemplos de uso por tipo de perfil. En todos los
casos las alertas son **orientativas** y requieren validación profesional.

## Ayuntamientos y gobiernos locales

- **Detección temprana de incrementos** en señales locales (urgencias,
  gastroenteritis, golpe de calor) para activar protocolos municipales.
- **Coordinación con salud pública** ante avisos: el mapa muestra por provincia la
  severidad y la explicación de cada alerta.
- **Episodios de calor extremo:** combinar la señal de golpe de calor con avisos
  meteorológicos (cuando AEMET esté configurado) para planes locales de calor.
- Importar series propias agregadas vía `import-csv` para vigilarlas en el mismo
  panel, sin exponer datos personales.

## Centros de salud y atención primaria

- **Contexto poblacional** del territorio (incidencia de gripe, positividad de
  COVID-19, ingresos por VRS) para anticipar presión asistencial.
- **Seguimiento de temporada** de virus respiratorios mediante las capas temáticas
  del mapa (Gripe, COVID-19, VRS).
- Cargar agregados semanales propios (`manual_import`) para comparar con la
  tendencia y recibir alertas de subidas anómalas.

## Analistas de salud pública

- **Detección de anomalías** con varios métodos combinados (media móvil, z-score,
  z-score robusto mediana/MAD, baseline histórico, subida porcentual) y filtrado
  por modo, provincia, evento, señal y rango temporal.
- **Priorización por severidad** (low/medium/high/critical) y revisión del estado
  de cada alerta (`open` → `reviewed` / `dismissed`) vía API.
- **Trazabilidad**: cada alerta enlaza con las fuentes y muestra valor observado,
  baseline y explicación del método disparado.
- **Integración** con sus propios flujos mediante la API REST y exportación
  GeoJSON.

## Investigadores

- **Reutilización de datos abiertos** ya catalogados y normalizados (provincia,
  CCAA, evento, señal, unidad) sin tener que recolectar de cada portal.
- **Reproducibilidad**: base SQLite local, sin servicios externos obligatorios.
- **Escenarios controlados** con el motor de simulación (semilla, curva de brote,
  severidad) para validar métodos de detección sobre datos sintéticos conocidos.

## Docencia y formación

- **Modo simulación** con presets listos (`gripe_madrid`, `covid_barcelona`,
  `vrs_zaragoza`, `gastro_valencia`, `calor_sevilla`, `multi_evento`) para mostrar
  cómo se forma y detecta un brote, todo marcado como `SIMULACIÓN`.
- **Comparar métodos de detección** sobre las mismas series simuladas.
- **Aprender el flujo completo** de vigilancia: ingesta → normalización →
  detección → alerta → mapa, en local y sin datos personales.
- Posibilidad de **limpiar** las simulaciones (`clear-simulations`) y empezar de
  nuevo sin afectar a ningún dato real.
