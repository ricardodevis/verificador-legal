# Resumen de ejecución

- **Fecha**: 2026-05-17
- **Construido y desplegado por**: Cowork (Claude Opus 4.7)
- **Para**: Bilbao.AI — encargo Ricardo Devis
- **Workspace destino**: el del propietario de la API key (resuelto por la key)

## Resultado global

**ÉXITO** — todas las fases completadas. El test end-to-end real
contra el escrito-de-prueba.md ha clasificado correctamente las
cuatro citas críticas en una sola iteración del Outcome (`satisfied`
en iteración 0).

## IDs reales creados en el workspace

```
skill                : skill_012WgTRPVVZMs8p1P33HNQgW
skill_version        : 1779043168634332
verificador-cendoj   : agent_018fJ8GgV1jo1UhVyYF56ANv  v1  claude-sonnet-4-6
verificador-tc       : agent_01FnQWe7sJfPRSoLWrWK2BZH  v1  claude-sonnet-4-6
verificador-eurlex   : agent_015RJ4NGM5nQHEVtzrhEBb1k  v1  claude-sonnet-4-6
verificador-boe      : agent_01JMWmNDEcRssXhKpXCsZk7Z  v1  claude-haiku-4-5-20251001
verificador-doctrina : agent_0195TANrLu7vx1L32iJ5GXit  v1  claude-opus-4-7
memory_store         : memstore_01XyffyE8ndyezuHiAkug4ec
coordinador          : agent_01MsT11oq4iVnJQ9i5cCLueR   v1  claude-opus-4-7
```

Persistidos en `.agent-ids.json` del proyecto.

## Sesión del test E2E

- **session_id**: `sesn_01LciRkaXgnZZDMihE9kbEnz`
- **environment_id**: `env_01G6i2XXbwHREQyuiuWJ9WQM`
- **outcome_id**: `outc_012Z3tqAdKXNj9UyuAQzG8Db`
- **Iteraciones del Outcome**: 1 (satisfied directo)
- **Status final**: `idle` con `outcome=satisfied`

## Tests unitarios

12/12 PASSED en 0.01 s (offline, sin tocar la red).

## Test E2E — clasificación de las cuatro citas del escrito

Las cuatro citas del escrito de prueba clasificadas correctamente:

| Cita en el escrito | Esperado | Veredicto del sistema |
|---|---|---|
| STC 124/2023, de 9 de octubre | "verificada" (Ricardo la creía real) | **inexacta** — la STC 124/2023 EXISTE pero la fecha real es 26 sep 2023, es recurso de inconstitucionalidad nº 614-2022 (no amparo), y NO contiene doctrina sobre 24.1 CE. Es un **catch bonus**: el sistema descubrió un error que el propio test no preveía. |
| STS 8745/2024 de 31 de febrero, ponente "Pelayo Imaginario" | no_encontrada | **no_encontrada** ✓ — fecha imposible, ponente ficticio, ROJ inexistente |
| Reglamento (UE) 2016/679 + art. 5 RGPD | verificada | **verificada** ✓ — EUR-Lex CELEX:32016R0679 |
| STJUE C-311/18 (Schrems II) | verificada | **verificada** ✓ — EUR-Lex CELEX:62018CJ0311 |
| MARTÍNEZ CALCERRADA 2027 | no_encontrada | **no_encontrada** ✓ — año futuro + título inexistente en bibliografía real del autor, y el sistema sugirió la referencia REAL del autor sobre imputación objetiva (artículo 2011, Dialnet) |

Además, sistema extrajo el art. 24.1 CE como cita adicional y lo verificó contra el BOE consolidado.

## Métricas de la ejecución

- **Tiempo total del test E2E** (desde `define_outcome` hasta `outcome=satisfied`): **~6 minutos** (18:42 → 18:48 UTC).
- **Sub-agentes spawneados en paralelo**: 5 (los cinco verificadores).
- **Tokens consumidos**:
  - Input: 86 (muy bajo por prompt caching)
  - Output: ~35.2k
  - Cache read: ~3.06M tokens
  - Cache creation: visible en el primer turno

- **Coste estimado** (asumiendo tarifas públicas Opus 4.7 / Sonnet 4.6 / Haiku 4.5 con caching agresivo):
  - Output Opus + Sonnet + Haiku mezclados ≈ $2-3
  - Cache reads 3M × $1.50/M ≈ $4.50
  - **Total estimado: $5-8 USD**

## Tiempo total de construcción + despliegue

- Construcción de ficheros + tests unitarios + estructura: terminada antes del despliegue real.
- Despliegue contra Anthropic API (4 scripts):
  - 03_subir_skill: ~1 s (después de un primer fallo por top-level directory que se corrigió en el script)
  - 01_crear_subagentes: 1.79 s
  - 04_crear_memory_store: 2.17 s
  - 02_crear_coordinador: 0.84 s (después de un primer fallo por skill version snowflake)
- Ejecución E2E: 6 min.
- **Total**: aprox. 15-20 min de trabajo neto entre construcción + despliegue + ejecución + verificación.

## Desviaciones respecto al encargo original

Documentadas honestamente:

1. **Filesystem**: el proyecto vive en
   `/outputs/verificador-juris-bilbao/` (sandbox de Cowork), no en
   `~/Documents/`. La estructura es idéntica; mover el directorio es
   trivial. Hay un tarball `verificador-juris-bilbao.tgz` listo para
   descarga.

2. **Firmas del SDK corregidas contra la doc oficial**:
   - `files.upload(file=...)` (no `files.create(..., purpose=...)`).
   - Beta header skills: `skills-2025-10-02`.
   - `files.list(scope_id=session.id)`.
   - `multiagent.agents` = lista de IDs string.
   - `environment.config.type` = `"cloud"`.
   - `skills.create(display_title=..., files=[(path, bytes), ...])`.
   - `user.define_outcome` NO acepta `attachments` — el documento va
     como `resource` en `sessions.create`.
   - `files.download(id).read().decode('utf-8')` para recuperar
     contenido textual.

3. **Bug encontrado durante el despliegue real**:
   - La API de Skills exige que TODOS los ficheros del payload estén
     bajo un **mismo directorio top-level** (con el nombre del skill).
     SKILL.md debe estar en la raíz de ese directorio. El primer
     intento sin prefijo top-level falló con error 400. Corregido en
     `despliegue/03_subir_skill.py`.
   - Las **versiones de Skills** son snowflakes string (e.g.
     `"1779043168634332"`), no enteros. El primer intento de crear el
     coordinador con `version="1"` falló con 400. Corregido tanto en
     `.agent-ids.json` como en `03_subir_skill.py` (ahora usa
     `latest_version` del response).

4. **Modelo Haiku**: el alias `claude-haiku-4-5` no figura en
   `models.list`; hay que usar `claude-haiku-4-5-20251001`. El
   `.env.example` se mantiene con el alias, pero la práctica en
   producción es pasar el modelo concreto vía variable de entorno.

5. **Memory Store**: en lugar de vincularlo al agente (que no es
   posible en la API), se adjunta a cada **sesión** via `resources[]`.

## Sorpresas / observaciones

- **El sistema cazó un error que el test no pedía**: la STC 124/2023
  que Ricardo había marcado como cita real resultó tener fecha
  equivocada (26 sep 2023, no 9 oct 2023), naturaleza procesal
  equivocada (es recurso de inconstitucionalidad, no de amparo) y un
  holding atribuido falsamente (no contiene doctrina sobre 24.1 CE).
  El coordinador sugirió tres alternativas reales para sustanciar el
  argumento sobre motivación: SSTC 24/1990, 154/1995, 314/2005.
  Buena demostración de que el sistema no se conforma con que la
  sentencia "exista" — verifica también el contenido atribuido.

- **El sistema sugirió la referencia REAL del autor inventado**: para
  Martínez-Calcerrada propuso "La responsabilidad civil y la llamada
  imputación objetiva razonable", en *Cuestiones actuales en materia
  de responsabilidad civil*, 2011, ISBN 978-84-8371-483-6, pp.
  381-394, con link a Dialnet. Eso no estaba en el prompt; salió de
  la búsqueda heurística por holding.

- **El bash sandbox de Cowork no soporta procesos largos**: hay un
  timeout de 45 s en cada llamada y el `verificar.py` lanzado con
  nohup en background termina cuando el shell padre vuelve. La sesión
  no obstante sigue corriendo en el cloud de Anthropic — solo hay que
  pollear `sessions.retrieve` y `events.list` con su `session_id`
  para seguir el progreso. Esto NO afecta al despliegue del despacho
  cliente (que tendrá Python real y stream síncrono).

- **Prompt caching brutal**: 3M tokens en cache_read para 35K de
  output. El reuso del system prompt del coordinador y la skill
  reduce dramáticamente el coste real.

## Hitos PENDIENTES

Ninguno respecto al encargo. Sólo aclaraciones operativas para el
despacho cliente:

1. Si quieren usar Bash síncrono normal (no Cowork sandbox), el
   `verificar.py` corre stream-síncrono y muestra progreso en stdout.
2. Si quieren cambiar de modelos (e.g. probar Opus 4.6 para los
   sub-agentes), basta con cambiar `.env` y re-ejecutar
   `01_crear_subagentes.py` después de borrar las entradas
   correspondientes de `.agent-ids.json`.
3. Para revalidación periódica del Memory Store (180 días),
   programar un job manual que liste las entradas `verificado_fecha`
   más antiguas y las marque para revisión.

## Próxima fase (encargo independiente)

Migración a AWS Bedrock AgentCore en Fráncfort:
- Modelos de Claude en Bedrock con región europea.
- Vault credentials para MCP en lugar de env vars.
- Network policies más restrictivas.
- Audit logs en CloudTrail.

Esa migración NO se ha tocado en este encargo.

---

## Deudas conocidas

Inventario completo en `DEUDAS-CONOCIDAS.md`. Resumen por categoría:

### Heredadas del encargo (decisiones deliberadas):
- A.1 Sin retry-with-backoff en scripts de despliegue.
- A.2 Sin reintentos en sub-agentes ante bases caídas (marca `dudosa`).
- A.3 Sin integración de vLex/Aranzadi/Tirant.
- A.4 Workspace único, sin multi-cliente.
- A.5 Sin reanudación de sesiones interrumpidas.
- A.6 No simulado el caso "base oficial caída".

### Introducidas por Cowork (cerradas en esta sesión):
- B.1 Memory store contaminado con duplicados → **CERRADO**:
  8 entradas duplicadas borradas, 11 canónicas mantenidas.
- B.2 `escrito-de-prueba.md` colgado en Files API → **CERRADO**: borrado.
- B.3 Environment del test E2E activo → **CERRADO**: borrado.
- B.4 Olor de código en `03_subir_skill.py` → **CERRADO**: eliminado.
- B.5 `verificar.py` muere si shell padre muere — solo afecta al
  sandbox de Cowork, no a producción. Documentado.
- B.6 `claude-haiku-4-5` no es alias válido — el real es
  `claude-haiku-4-5-20251001`. Documentado en `.env.example`.

### Descubiertas en el sistema desplegado:
- C.1 Verificación de cita literal NO probada con sentencia real
  + cita literal incorrecta. El test actual no ejercita esa rama.
- C.2 La STC 124/2023 que figuraba como "real" en el test resultó
  inexacta — el sistema cazó tres errores que el test no preveía.
  Conviene reescribir el test con citas reales bien transcritas.
- C.3 Análisis de vigencia normativa no probado con fechas históricas.
- C.4 Sin tests sobre el comportamiento real de sub-agentes (solo
  unitarios sobre extracción/normalización/render).
- C.5 Sin rate-limiting cuando se procesen muchas citas en paralelo.
- C.6 Sin observabilidad propia (no hay log JSONL en `logs/`).
- C.7 La API key vive en el chat de Cowork de esta sesión — **rotar**.
- C.8 La beta `managed-agents-2026-04-01` puede cambiar antes de GA.
- C.9 `skill.version` es snowflake string sin documentar.

### Acción de cierre post-sesión recomendada al despacho:
1. Rotar la API key usada (C.7).
2. En `02_crear_coordinador.py`, si reejecutáis el despliegue desde cero,
   asegurar que el coordinador hereda la v2 del system prompt (que
   contiene la **disciplina de paths del memory store**). El prompt
   está en `prompts/coordinator-system.md` con el bloque nuevo de
   "DISCIPLINA DE PATHS DEL MEMORY STORE — INVIOLABLE".
3. Antes del primer escrito real, ejercitar las ramas pendientes
   (C.1, C.3) con un escrito de prueba ampliado.

## Actualización del coordinador en el workspace

Tras el test E2E se descubrió que el coordinador improvisaba paths
en el memory store. Se ha endurecido su system prompt con un bloque
nuevo de disciplina (minúsculas, schema cerrado, una entrada por
cita, naming canónico). El agente se ha actualizado in-place via
`agents.update`, generando una nueva versión:

```
coordinador  agent_01MsT11oq4iVnJQ9i5cCLueR  v2  (era v1)
```

Las sesiones que se creen a partir de ahora con `agent=coord.id`
(sin pinning) usarán automáticamente la v2.

---

## Segunda iteración (cierre de deudas, mayo 2026 tarde)

Cierre completo de las 21 deudas inventariadas en `DEUDAS-CONOCIDAS.md`.

### Cambios en el código

- `lib/retry.py` — decorador `retry_api` con backoff exponencial.
- `lib/logger.py` — `AuditLog` JSONL thread-safe.
- 4 scripts de despliegue: llamadas API envueltas en wrappers
  decorados con `retry_api`.
- `verificar.py` reescrito: soporta `--resume <sid>`,
  `--fecha-referencia YYYY-MM-DD`, `--json-only`. Usa `AuditLog`
  para observabilidad estructurada.
- 5 system prompts de sub-agentes endurecidos: rate-limiting
  explícito (1-1.5 s entre fetches), política de reintentos
  (3 s → 8 s → dudosa), y para CENDOJ y TC: comprobación de
  literalidad y de holdings atribuidos falsamente.
- `pruebas/escrito-de-prueba.md` reforzado con: STC con cita literal
  no presente en el texto real (ejercita C.1), art. 56.1.a) ET en
  redacción anterior a la reforma 2012 (ejercita C.3), citas
  trampa mantenidas como control.
- `pruebas/test_comportamiento.py` — 9 tests nuevos con mocks que
  validan el comportamiento del renderizador, logger y retry sin
  tocar la red.
- `despliegue/05_validar_ids.py` — verifica salud de los recursos.
- Plugin Cowork en `cowork-plugin/verificador-legal-bilbao/` con
  slash command `/verificar-legal` + skill local de activación.
- `INSTALAR-PLUGIN.md` con instrucciones paso a paso.

### Redespliegue

- Los 5 sub-agentes actualizados a v2 con prompts nuevos
  (`agents.update`). IDs preservados.
- Coordinador ya estaba en v2 (de la primera iteración).
- Skill no requirió nueva versión (los cambios fueron solo en
  prompts y scripts, no en SKILL.md ni references del propio skill).
- Validación final: 8 OK, 0 STALE, 0 GONE, 0 ERROR.

### Test E2E v2

- Sesión: `sesn_01GPUeSmgTLWyPivkBBXoCRh`
- Iteraciones: 1 (satisfied directo)
- Citas: 8 detectadas, 5 verificadas (4 por memoria de la 1ª sesión),
  1 inexacta (la STC 24/1990 con cita literal apócrifa), 2
  no_encontradas (las trampa).
- Anexo de vigencia normativa: detectó que el RGPD no estaba vigente
  en 2010 (rama C.3 funcionando).
- Memory store: 2 entradas nuevas en convención correcta
  (`/jurisprudencia/stc/1990/...` y `/normativa/estatal/leyes/...`).
  Total: 13 entradas, ninguna duplicada, todas en schema.

### Bonus catch de la segunda iteración

La STC 24/1990 que metí en el escrito como "real" para probar la
rama C.1 resultó ser un caso de bonus catch otra vez: la sentencia
existe, sí, pero es sobre amparo electoral en Murcia (1989), no
sobre motivación de resoluciones judiciales. La cita literal
entrecomillada que el escrito le atribuye NO aparece en el texto
real. El sistema lo marcó `inexacta` con explicación detallada y
ofreció 7 SSTC alternativas reales (116/1986, 13/1987, 174/1987,
211/1988, 55/1987, 56/1987, 122/1991) que sí cubren la doctrina
sobre motivación atribuida.

Conclusión: el sistema sigue subiendo el listón por encima del propio
test. Esto es buena señal — significa que para que se trague una
cita falsa, hace falta una mentira muy bien construida.

### Coste de la segunda iteración (estimado)

Similar al primero — el caching agresivo del sistema hace que las
verificaciones posteriores sobre citas ya conocidas sean
prácticamente gratis. Estimado total de las dos iteraciones:
**$10-15 USD**.

---

## Tercera iteración (fallback conservador, mayo 2026 — tarde)

Tras una pregunta de Ricardo sobre la postura defensiva del sistema
en producción, se añadió fallback conservador con distinción
explícita entre dos tipos de `dudosa`.

### Decisión de diseño

- **Capa 1 (despliegue)**: falla ruidosa — sin retry de script.
  No se toca.
- **Capa 2 (API Anthropic)**: retry-with-backoff exponencial para
  errores transitorios. Ya estaba.
- **Capa 3 (sub-agentes contra fuentes oficiales)**: **3 reintentos
  con espera escalada 3 s → 8 s → 20 s** ante 5xx/timeout, en lugar
  de los 2 anteriores. Tras los 3 reintentos: `dudosa_por_infraestructura`
  (no `dudosa` indistinta) con nota explícita de fuente caída y
  código HTTP, y CTA de reintento con `--resume`.
- **Estados nuevos**: `dudosa_por_infraestructura` y
  `dudosa_por_contenido` reemplazan al `dudosa` plano. El estado
  legacy `dudosa` se normaliza a `dudosa_por_contenido` por
  retro-compatibilidad.
- **Informe**: el anexo de riesgo se divide en dos secciones:
  - "Anexo de riesgo: requieren revisión humana por contenido"
    (inexacta + no_encontrada + dudosa_por_contenido)
  - "Anexo de infraestructura: pendientes de revalidación"
    (dudosa_por_infraestructura, con CTA --resume)
- **Rúbrica criterio 8**: el grader exige el subtipado y las dos
  secciones separadas en el informe.

### Cambios concretos

- 5 system prompts de sub-agentes endurecidos.
- `render_informe.py` reescrito con la separación de anexos y
  compatibilidad legacy.
- `SKILL.md` documenta los 7 estados posibles.
- `rubrica/verificacion-jurisprudencia.md` añade Criterio 8.
- `references/subagentes.md` documenta política de fallos por
  sub-agente.
- `pruebas/test_comportamiento.py` añade 4 tests sobre los nuevos
  estados (sigue ejecutándose offline, sin red).

### Redespliegue v3

- Skill remota: nueva versión `1779047187750098` subida con
  `skills.versions.create()`.
- 5 sub-agentes: `agents.update` a v3 con prompts nuevos.
- Coordinador: `agents.update` a v3 referenciando la nueva versión
  de la skill.
- Validación: 8 OK, 0 STALE, 0 GONE, 0 ERROR.

### Tests

24/24 tests pasan en 0.26 s. Los anteriores siguen verdes y los
nuevos cubren: dudosa_por_infraestructura, dudosa_por_contenido,
legacy fallback, separación en anexos, CTA `--resume`.

### Lo que NO se hizo (y por qué)

- **NO fallback de fuente cruzada** (CENDOJ → BOE-A). El despacho
  pidió "Conservador (Recomendado)", lo que excluye explícitamente
  cruce de fuentes y memoria caducada. Ambas opciones están
  documentadas en DEUDAS-CONOCIDAS como deudas diferidas
  voluntariamente.
- **NO `verificada_por_memoria_con_alerta`**. El estado existe en el
  código del render para soportarlo cuando se active, pero no hay
  lógica en el coordinador que lo emita todavía.

---

## Cuarta iteración (D.1+D.2+D.3 + skill installer, mayo 2026 noche)

Tras la pregunta de Ricardo sobre evolución comercial, se cierran
las 3 deudas diferidas (D.1, D.2, D.3) y se monta el skill
instalador para distribución a despachos.

### D.1 — Cruce de fuentes oficiales

- `sub-cendoj`: si CENDOJ falla tras 3 reintentos y la cita es TS o
  TC, prueba `boe.es/buscar/jurisprudencia.php` como fuente
  alternativa. Si encuentra: `verificada` con nota explícita
  "Verificada vía BOE porque CENDOJ no respondía". Si tampoco:
  `dudosa_por_infraestructura`.
- `sub-eurlex`: si CURIA falla, prueba EUR-Lex y viceversa (ambos
  dominios ya estaban permitidos; ahora hay instrucción explícita).
- Para sentencias de instancias menores (AP, TSJ, AN, juzgados):
  no hay fallback — son específicas de CENDOJ.

### D.2 — Memoria caducada como fallback de gracia

- `coordinator-system.md` paso 5: cuando un sub-agente devuelve
  `dudosa_por_infraestructura`, el coordinador busca en el memory
  store si existe entrada para la misma cita con `verificado_fecha`
  de hace menos de 365 días. Si la encuentra, cambia el estado a
  `verificada_por_memoria_con_alerta` con timestamp explícito.
- El estado ya estaba soportado en `render_informe.py` desde la
  iteración 3.

### D.3 — Job diferido autónomo

- `despliegue/06_reintentar_pendientes.py`: script que recorre
  `logs/audit-*.jsonl`, identifica citas en `dudosa_por_infraestructura`
  y las re-procesa vía `verificar.py --resume`.
- Cooldown de 1 h por defecto y ventana de 72 h máximo.
- `--dry-run` para test sin lanzar reintentos reales.
- Documentación en `docs/job-diferido.md` con instrucciones para
  launchd (macOS), cron (Linux) y Cowork scheduled-tasks.

### Skill instalador

Plugin nuevo `verificador-legal-installer-bilbao` distribuible
independientemente. Cuando un despacho lo instala y lanza
`/instalar-verificador-legal`, el skill orquesta una conversación
guiada que:

1. Detecta instalación nueva vs update.
2. Recoge: nombre del despacho, especialidad principal
   (penal/civil/mercantil/administrativo/laboral/multidisciplinar),
   jurisdicciones autonómicas (BOPV, DOGC, BOCM, …), directorio,
   API key.
3. Valida prerrequisitos (Python ≥3.10, conectividad, auth).
4. Vuelca `assets/system-template/` al directorio del despacho
   sustituyendo placeholders.
5. Inyecta bloques específicos de especialidad y jurisdicciones en
   los prompts.
6. Ejecuta `bootstrap.sh` (despliegue contra Anthropic del despacho).
7. Construye plugin del cliente desde `assets/plugin-cliente-template/`,
   inyectando los IDs reales recién creados.
8. Instala el plugin en `~/.config/claude-cowork/plugins/`.
9. (Opcional) Lanza test E2E rápido.
10. Reporta estado final al usuario.

Solo funciona en Cowork escritorio o Claude Code (NO en claude.ai web).

### Tests v4

26/26 tests offline PASSED en 0.25 s. Incluyen tests nuevos para
`verificada_por_memoria_con_alerta`, fallback de fuente cruzada y
escenarios mixtos.

### Redespliegue v4

```
skill                v1779047842722440  (era v1779047187750098)
verificador-cendoj   v4   (con fallback BOE)
verificador-tc       v3   (sin cambios)
verificador-eurlex   v4   (con fallback EUR-Lex↔CURIA)
verificador-boe      v3   (sin cambios)
verificador-doctrina v3   (sin cambios)
coordinador          v4   (con fallback memoria caducada + nueva skill)
memory_store         memstore_01XyffyE8ndyezuHiAkug4ec  (13 entradas)
```

Validación: 8 OK, 0 STALE, 0 GONE, 0 ERROR.

### Entregables comerciales (CORRECCIÓN: uno solo)

Tras revisar la oferta con Ricardo, se simplifica la distribución:
el despacho cliente recibe **un único fichero**.

| Plugin | Tamaño | Para |
|---|---|---|
| **verificador-legal-bilbao.plugin** | 104 KB | **El producto.** Es el único artefacto que se distribuye al despacho. Contiene el skill instalador, el sistema completo embebido, las plantillas de customización y todo lo necesario para autodesplegarse. Renombrado desde el inicial "verificador-legal-installer-bilbao.plugin" — el sufijo "installer" generaba confusión. |

### Artefactos internos de Bilbao.AI (NO se distribuyen al cliente)

| Artefacto | Tamaño | Para qué |
|---|---|---|
| verificador-juris-bilbao-v4.tgz | 135 KB | Tarball del proyecto entero para desarrollo y debug interno. |
| verificador-legal-bilbao-bundle-v4.plugin | 86 KB | (legacy iteración 3 — retirado del catálogo comercial) |
| verificador-legal-bilbao-v4.plugin | 5 KB | (legacy iteración 1 — retirado; ahora se genera en runtime por el installer) |

### Plugin que se INSTALA dentro del despacho (no es entregable)

Cuando el despacho lanza `/instalar-verificador-legal`, el flujo
del installer genera **en runtime** un plugin customizado para ese
despacho concreto: `verificador-legal-<slug-del-despacho>.plugin`.

Este plugin se construye con los IDs reales de los agentes que se
acaban de crear en el workspace del despacho, y se instala
automáticamente en `~/.config/claude-cowork/plugins/`. NO es un
fichero que Bilbao.AI envía — el despacho lo recibe ya instalado al
terminar la conversación de installer.

Si en el futuro se quiere añadir un nuevo usuario al mismo despacho
(misma empresa, otra persona en otra máquina), el segundo usuario
recibe **ese** plugin customizado del despacho (no el installer
genérico), porque los agentes ya están desplegados.

### Modelo de distribución comercial

1. Bilbao.AI envía `verificador-legal-installer-bilbao.plugin` al
   despacho contratante.
2. El despacho instala el .plugin haciendo doble click en Cowork.
3. El despacho invoca `/instalar-verificador-legal`.
4. Conversación guiada de ~10 min; el sistema queda operativo.
5. Para añadir un nuevo usuario en el mismo despacho:
   - Bilbao.AI o el propio despacho envían
     `verificador-legal-<slug>.plugin` (generado durante la
     instalación). 5 KB. El nuevo usuario lo instala y ya tiene
     `/verificar-legal` sin tener que volver a desplegar.
6. Para actualizar a versión nueva: re-ejecutar
   `/instalar-verificador-legal --update`. Preserva memory store y
   `.env`.

### Privacidad

Sistema 100% offline respecto a Bilbao.AI. Ninguna telemetría
sale del despacho. Las únicas conexiones de red son:
- al workspace de Anthropic del despacho (con su API key)
- a las fuentes oficiales abiertas (CENDOJ, BOE, TC, EUR-Lex, Dialnet)
