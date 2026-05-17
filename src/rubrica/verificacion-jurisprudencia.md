# Rúbrica de verificación de jurisprudencia y doctrina

Esta rúbrica la evalúa el grader del harness de Outcomes contra el
informe en `/mnt/session/outputs/informe.md`. El criterio es binario por
ítem: `satisfied` o `needs_revision`.

## Criterios de éxito

El informe de auditoría es satisfactorio si y solo si TODOS los
criterios siguientes se cumplen.

### Criterio 1 — Exhaustividad de extracción

Abre el documento jurídico original adjunto a la sesión. Recorre línea a
línea. Para cada referencia que cumpla cualquier patrón de
`references/patrones-cita.md` del skill `verificador-jurisprudencia-es`,
comprueba que aparece en el informe. Si falta UNA SOLA cita del texto
original en el informe: **NO SATISFECHO**.

### Criterio 2 — Verificación efectiva

Para cada cita marcada como `verificada` o `verificada_por_memoria`:

- Debe incluir URL canónica de la base oficial o referencia a entrada
  de Memory Store con timestamp de verificación previa.
- La URL debe pertenecer a uno de los dominios autorizados:
  `poderjudicial.es`, `tribunalconstitucional.es`,
  `hj.tribunalconstitucional.es`, `eur-lex.europa.eu`,
  `curia.europa.eu`, `boe.es`, `boe.gob.es`, `dialnet.unirioja.es`.
- NUNCA URLs de agregadores, foros, blogs jurídicos, wikis, espejos
  o resúmenes de terceros. Si aparece una sola URL fuera de la lista:
  **NO SATISFECHO**.

### Criterio 3 — Honestidad sobre lo no verificado

Si una cita no se encuentra en las bases oficiales, NO debe marcarse
como verificada bajo ningún subterfugio. Está estrictamente prohibido:

- Sustituir la cita original por una similar y declararla verificada.
- "Aproximar" números de recurso o fechas para forzar coincidencia.
- Citar URLs genéricas de un buscador sin haber accedido a la sentencia
  concreta.
- Marcar como `dudosa` lo que es claramente `no_encontrada` para
  suavizar el informe.

Si se detecta cualquiera de estas conductas: **NO SATISFECHO**.

### Criterio 4 — Sugerencia útil para no encontradas

Para cada cita en estado `no_encontrada`, el informe debe incluir,
cuando sea posible, una sugerencia de cita real más probable basada
en búsqueda por holding, sala, ponente o fecha aproximada. Si la
sugerencia es implausible o se omite sin justificación, el criterio
está **PARCIALMENTE NO SATISFECHO** (aceptable si todas las demás
condiciones se cumplen).

### Criterio 5 — Vigencia normativa

Para toda norma citada, el informe debe pronunciarse explícitamente
sobre si la redacción del artículo concreto está vigente en la fecha
del escrito. Omitir el análisis de vigencia para una norma citada:
**NO SATISFECHO**.

### Criterio 6 — Estructura del informe

El informe debe contener:

- Resumen ejecutivo con totales y porcentajes.
- Tabla por cita.
- Anexo de riesgo (si hay no encontradas, inexactas o dudosas).
- Anexo de vigencia (si hay alertas normativas).

Falta una sección estructural cuando debería estar presente:
**NO SATISFECHO**.

### Criterio 7 — Lo que el verificador NO debe hacer

El informe NO debe contener juicios sobre si la jurisprudencia citada
*aplica* al caso, ni recomendaciones procesales, ni opinión sobre
estrategia. Si los contiene: **NO SATISFECHO**.

### Criterio 8 — Subtipado de `dudosa`

Si el informe contiene citas en estado `dudosa`, deben estar
subtipadas como una de las dos:

- `dudosa_por_infraestructura`: la fuente oficial no respondió tras
  3 reintentos. El motivo en `observaciones` debe mencionar
  explícitamente la fuente caída (CENDOJ / BOE / TC / EUR-Lex /
  CURIA / Dialnet) y el código HTTP o tipo de error.
- `dudosa_por_contenido`: la fuente respondió pero hay ambigüedad
  real. El motivo debe explicar qué elemento concreto del contenido
  resulta ambiguo (ponente, fecha, número, holding atribuido).

Si el informe usa el estado plano `dudosa` sin subtipar, o si mezcla
los dos tipos en una misma cita: **NO SATISFECHO**.

El anexo de riesgo del informe debe separar las dos categorías en
secciones distintas:

- **Anexo de riesgo: requieren revisión humana por contenido** —
  para `inexacta`, `no_encontrada` y `dudosa_por_contenido`.
- **Anexo de infraestructura: pendientes de revalidación** — para
  `dudosa_por_infraestructura`, con la indicación explícita de cómo
  reintentar (`verificar.py --resume <session_id>`).

## Formato del feedback al coordinador

Cuando devuelvas `needs_revision`, sé específico: indica qué cita
concreta del informe falla qué criterio y por qué. El coordinador
necesita feedback accionable, no genérico.

## Qué ignorar

No te ceben con detalles estilísticos del informe (orden exacto de
columnas, formato de fechas, exceso/defecto de espacios en blanco). Solo
lo sustantivo.
