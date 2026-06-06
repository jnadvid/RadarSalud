# Privacidad y ética

RadarSalud es una herramienta de **vigilancia poblacional con datos abiertos
agregados**. Su diseño parte de un compromiso ético explícito.

## Principios

- **Solo datos abiertos y agregados.** RadarSalud trabaja con señales poblacionales
  agregadas por territorio y fecha, nunca a nivel individual.
- **Sin datos personales.** No se almacenan ni procesan datos personales. La
  importación de CSV rechaza columnas como `dni`, `nif`, `nie`, `email`, `correo`,
  `telefono`, `movil`, `nombre`, `apellidos`, `direccion`, `historia_clinica`,
  `paciente`, `tarjeta_sanitaria`, `iban`, etc., y detecta de forma heurística
  DNIs, correos y teléfonos en texto libre, rechazando la importación.
- **No es una herramienta de diagnóstico.** Las señales y alertas son indicadores
  poblacionales, no diagnósticos clínicos.
- **No sustituye a profesionales sanitarios** ni a la autoridad de salud pública.
- **Posibilidad de falsos positivos y negativos.** La detección estadística de
  anomalías puede equivocarse; las alertas son orientativas.
- **Requiere validación de salud pública.** Toda alerta debe ser interpretada y
  validada por personal cualificado antes de cualquier decisión.
- **Trazabilidad de fuentes.** Cada observación guarda su `source_id` y cada
  alerta los `source_ids` que la fundamentan, para poder auditar el origen.
- **Limitaciones de los datos abiertos.** Cobertura desigual, retrasos de
  publicación, cambios de formato y heterogeneidad entre administraciones afectan
  a la calidad y comparabilidad de las señales.

## Cómo se hacen cumplir estos principios

- La importación CSV valida ausencia de columnas/valores personales antes de
  insertar nada (`utils/validation.py`).
- Solo se permiten eventos y tipos de señal de una lista cerrada (gripe, covid,
  vrs, gastroenteritis, golpe_calor, calidad_aire, mortalidad, urgencias...).
- Los conectores respetan términos de uso y aplican cortesía de red; no se hace
  scraping agresivo ni se inventan URLs.
- El modo simulación está siempre separado y marcado como `SIMULACIÓN`, para no
  confundir datos sintéticos con reales.
- La aplicación declara en su propia descripción: *"No usa datos personales. No
  diagnostica. No sustituye a profesionales sanitarios."*

## Uso responsable

Las alertas de RadarSalud son una **ayuda exploratoria** para detectar posibles
incrementos anómalos en señales abiertas. No deben usarse como base única para
decisiones sanitarias, comunicaciones públicas ni medidas que afecten a personas
o colectivos sin la validación de la autoridad de salud pública competente.
