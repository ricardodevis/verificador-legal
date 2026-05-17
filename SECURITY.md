# Política de Seguridad

## Cómo reportar una vulnerabilidad

Si has descubierto una vulnerabilidad de seguridad en este proyecto,
**por favor NO la reportes a través de un issue público de GitHub**.

En su lugar, envía un email a **`ricardo@bilbao.ai`** con:

- Descripción de la vulnerabilidad.
- Pasos para reproducirla.
- Versión afectada (`v1.0.0`, `main`, etc.).
- Tu nombre o alias para el reconocimiento (opcional).

Responderé en un plazo máximo de **48 horas hábiles**.

## Política de divulgación

- Trabajaremos contigo para entender y resolver el problema antes
  de hacerlo público.
- Acreditaremos tu descubrimiento en el `CHANGELOG.md` (si así lo
  deseas) cuando publiquemos el fix.
- No tomaremos acciones legales contra investigadores de seguridad
  de buena fe.

## Áreas sensibles del proyecto

Los siguientes componentes son **críticos** por su naturaleza:

### 1. Manejo de la API key

- La API key del despacho cliente vive en `.env` local con
  permisos `600`.
- **Nunca debe** aparecer en logs, outputs del informe, audit JSONL,
  ni en ningún fichero subido a Anthropic Files API.
- Cualquier ruta de código que pueda filtrarla es una vulnerabilidad
  crítica.

### 2. Escritos del despacho

- Los escritos jurídicos del despacho pueden contener información
  sujeta a **secreto profesional**.
- Se suben temporalmente a Anthropic Files API durante la
  verificación. Su retención y borrado se rigen por la política de
  Anthropic.
- Si encuentras una ruta donde el contenido del escrito termine en
  un lugar no previsto (logs, telemetría, terceros), es
  vulnerabilidad alta.

### 3. Memory store

- El memory store puede contener resúmenes y citas de los asuntos
  del despacho.
- Aislamiento entre despachos: cada workspace de Anthropic es
  independiente. Si encuentras una forma de que un despacho acceda
  al memory store de otro, es vulnerabilidad crítica.

### 4. Plugin de Cowork

- El plugin instalador `verificador-legal-bilbao.plugin` ejecuta
  código en la máquina del usuario.
- Si encuentras una forma de inyectar código malicioso a través de
  la conversación del instalador, es vulnerabilidad alta.

## Compromiso de no-actividad agresiva

Los **sub-agentes** de este proyecto consultan fuentes oficiales
(CENDOJ, BOE, TC, EUR-Lex, Dialnet) con rate-limit explícito
(1-1.5 s entre fetches, máximo 3 reintentos por cita). Cualquier
parche que elimine estos rate-limits o convierta el sistema en
agresivo contra estas fuentes públicas **se rechazará**.

## Versiones soportadas

| Versión | Soporte de seguridad |
|---|---|
| 1.0.x | ✅ Actualizaciones de seguridad |
| < 1.0 (iteraciones internas) | ❌ No |
