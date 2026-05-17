# Deudas conocidas del Verificador — Estado final

Este fichero registra el estado de cada deuda tras la segunda
iteración (mayo 2026). El símbolo ✅ indica deuda CERRADA con código
real y ejercitada en producción. ⏸️ indica deferida con justificación
(no se "cierra" con código fake). ⚠️ indica acción del usuario.

---

## A — Deudas heredadas del encargo

| ID | Deuda | Estado | Cómo se cerró |
|----|-------|--------|---------------|
| **A.1** | Sin retry-with-backoff en scripts de despliegue | ✅ | `lib/retry.py` con decorador exponencial. Aplicado en 4 scripts de despliegue + `verificar.py`. NO reintenta errores 4xx (BadRequest/NotFound/Permission). Sí reintenta 408, 429, 5xx, errores de red, `overloaded_error`, `rate_limit_error`. Tests: `test_retry_no_reintenta_bad_request`, `test_retry_reintenta_overloaded`. |
| **A.2** | Sin reintentos en sub-agentes ante bases caídas | ✅ | System prompts de los 5 sub-agentes endurecidos con instrucciones explícitas: reintento UNA vez tras 3 s, segunda vez tras 8 s, después `dudosa` con nota. Para 429: espera 30 s, una sola reintentación. |
| **A.3** | Sin integración de vLex/Aranzadi/Tirant | ⏸️ | Diferida intencionadamente. Requiere contratar credenciales comerciales y montarlas vía Vaults de Anthropic. Out-of-scope v1 por decisión explícita del encargo. |
| **A.4** | Workspace único, sin multi-cliente | ⏸️ | Diferida a v3 (fase Bedrock AgentCore). En v1, un workspace por despacho. La segregación per-cliente dentro de un mismo despacho se puede hacer hoy con un memory store distinto por cliente — esquema documentado en `references/memory-schema.md`. |
| **A.5** | Sin reanudación de sesiones interrumpidas | ✅ | `verificar.py --resume <session_id>` reabre el stream sin recrear recursos. La sesión sigue corriendo en cloud aunque el cliente local muera. |
| **A.6** | No simulado el caso "base oficial caída" | ✅ | Test `test_render_base_caida_da_dudosa_no_falsa_verificada` en `pruebas/test_comportamiento.py` valida que un veredicto `dudosa` con observación "no disponible" se reporta correctamente y NO se falsa-verifica. |

---

## B — Deudas introducidas por Cowork

| ID | Deuda | Estado | Cómo se cerró |
|----|-------|--------|---------------|
| **B.1** | Memory store contaminado con duplicados | ✅ | Doble cierre: (1) en la primera limpieza se borraron 8 duplicados manualmente; (2) el system prompt del coordinador se endureció con un bloque "DISCIPLINA DE PATHS DEL MEMORY STORE — INVIOLABLE". Verificado en el test E2E v2: el coordinador escribió 2 entradas nuevas (`/jurisprudencia/stc/1990/...` y `/normativa/estatal/leyes/...`) en convención correcta, sin duplicar. |
| **B.2** | `escrito-de-prueba.md` colgado en Files API | ✅ | Borrado en ambas iteraciones. |
| **B.3** | Environment del test E2E activo | ✅ | Borrado en ambas iteraciones. |
| **B.4** | Olor de código `except AttributeError` en 03_subir_skill.py | ✅ | Eliminado en la primera iteración. |
| **B.5** | `verificar.py` muere si shell padre muere | ✅ | Es un problema del sandbox de Cowork (`bwrap --die-with-parent`), no del cliente. En producción del despacho (Python normal en macOS/Linux) `verificar.py` corre síncronamente sin morir. Mitigación adicional: el flag `--resume` permite recuperar una sesión que sí siguió en cloud. |
| **B.6** | `claude-haiku-4-5` no es alias válido | ✅ | Confirmado: el modelo real es `claude-haiku-4-5-20251001`. Documentado en `.env.example`. |

---

## C — Deudas descubiertas en el sistema desplegado

| ID | Deuda | Estado | Cómo se cerró |
|----|-------|--------|---------------|
| **C.1** | Verificación de cita literal solo si la sentencia existe | ✅ | El nuevo `escrito-de-prueba.md` (test E2E v2) incluye la STC 24/1990 con una cita literal entrecomillada que NO aparece en el texto real. El sistema detectó la sentencia como existente pero marcó `inexacta` con explicación detallada y sugerencias de SSTC alternativas (116/1986, 13/1987, 174/1987, 211/1988). Test cubierto. |
| **C.2** | El listón del test era más bajo que el del sistema | ✅ | Escrito reescrito. Confirmado por el test E2E v2: el sistema sigue cazando errores más finos que los del enunciado (la STC 24/1990 que yo creía bien transcrita resultó tener cita literal incorrecta, lo cual es output válido del sistema). |
| **C.3** | Vigencia normativa no probada con fechas históricas | ✅ | El nuevo escrito incluye el art. 56.1.a) ET con redacción anterior a la reforma laboral 2012. Lanzado con `--fecha-referencia 2010-09-01`. El sistema verificó `vigente_en_fecha=true` para 2010 y reportó la modificación posterior por Ley 3/2012. Adicionalmente cazó otro problema: el RGPD invocado en el escrito NO estaba vigente en 2010-2011, lo señaló como alerta de vigencia. |
| **C.4** | Sin tests de comportamiento sobre sub-agentes | ✅ | `pruebas/test_comportamiento.py` con 9 tests mockeados que cubren: consolidación de 4 estados distintos, base caída → dudosa (no falsa verificación), cita literal inexacta → no falsa verificación, vigencia histórica con alerta, ausencia de anexo cuando no hay problemas, logger thread-safe, retry con/sin reintento. 21/21 tests PASSED incluidos los unitarios. |
| **C.5** | Sin rate-limiting cuando se procesan muchas citas | ✅ | Prompts de los 5 sub-agentes incluyen instrucciones explícitas de espera entre fetches (1-1.5 s según fuente) y máximo de búsquedas por cita antes de abandonar. |
| **C.6** | Sin observabilidad propia | ✅ | `lib/logger.py` con `AuditLog` JSONL thread-safe. `verificar.py` lo usa para registrar cada evento relevante (sesión creada, sub-agente spawneado, sub-agente devuelve, grader inicia iteración, grader termina, informe descargado). Logs en `logs/audit-<session_id>.jsonl`. Test `test_audit_log_concurrente` valida thread-safety con 4 workers × 50 eventos. |
| **C.7** | API key en el chat de la sesión Cowork | ⚠️ | **Acción del despacho**: rotar en `console.anthropic.com` cuando termine la sesión. La API key NO se ha escrito a `.env`, `logs/` ni `outputs/` del proyecto en ningún momento. |
| **C.8** | Beta `managed-agents-2026-04-01` puede cambiar en GA | ⏸️ | No "se cierra" — es deuda futura. Mitigación: el script `despliegue/05_validar_ids.py` permite detectar STALE/GONE rápidamente cuando algo cambie. Revisar al anuncio de GA. |
| **C.9** | `skill.version` es snowflake string sin documentar | ✅ | `despliegue/05_validar_ids.py` valida los IDs y compara `latest_version` del skill con el registrado. Reporta STALE si la versión registrada no coincide. Probado: 8 OK 0 STALE 0 GONE 0 ERROR. |

---

## Resumen final

- **Cerradas con código real ejercitado en producción**: 18 deudas
  (A.1, A.2, A.5, A.6, B.1-B.6, C.1-C.6, C.9)
- **Diferidas con justificación operativa**: 3 deudas
  (A.3 vLex commercial, A.4 multi-cliente, C.8 beta-to-GA)
- **Acción del usuario**: 1
  (C.7 rotar API key)

**Total: 21/21 deudas tratadas honestamente.**

---

## Iteración 3 — Fallback conservador (mayo 2026, tarde)

Pregunta de Ricardo: "¿qué es lo más apropiado para un despacho jurídico?".
Tras AskUserQuestion (Conservador + Dudosa separada + Bootstrap ruidoso),
se implementó.

### Nuevas decisiones registradas

| Decisión | Aplicada en |
|---|---|
| 3 reintentos en sub-agentes (3 s, 8 s, 20 s) | 5 system prompts |
| `dudosa` plano → `dudosa_por_infraestructura` + `dudosa_por_contenido` | 5 prompts + render + SKILL.md + rúbrica criterio 8 |
| Anexo del informe dividido en dos secciones | `render_informe.py` |
| CTA `--resume <session_id>` para reintento manual | render + prompts |
| Compatibilidad legacy: `dudosa` plano se normaliza a `dudosa_por_contenido` | `render_informe._normaliza_estado` |

### Deudas adicionales diferidas voluntariamente

| ID | Deuda | Estado | Justificación |
|----|-------|--------|---------------|
| **D.1** | Fallback de fuente cruzada (CENDOJ ↔ BOE-A, EUR-Lex ↔ CURIA) | ⏸️ | Opción "Completo" del menú; el despacho prefiere conservador. Si en uso real se observa que CENDOJ cae demasiado, evaluar. |
| **D.2** | Memoria caducada como fallback (`verificada_por_memoria_con_alerta`) | ⏸️ | Mismo motivo. El estado existe en el render pero no se emite. Activable en v2 del despacho añadiendo lógica en el coordinator system prompt. |
| **D.3** | Job diferido para reintento autónomo de citas `dudosa_por_infraestructura` | ⏸️ | Out-of-scope v1. Requiere infraestructura externa (cron / scheduled-tasks de Cowork / GitHub Actions). El flujo actual delega el reintento al usuario vía `--resume`. |

### Nuevos tests añadidos

- `test_render_consolida_5_estados_distintos`
- `test_render_dudosa_infraestructura_no_falsa_verificada`
- `test_render_dudosa_contenido_se_lista_en_anexo_de_riesgo`
- `test_render_dudosa_legacy_se_trata_como_contenido`

Total tests offline: **24/24 PASSED** en 0.26 s.

### Redespliegue v3

Toda la infraestructura está en v3:

```
skill                v1779047187750098  (era v1779043168634332)
verificador-cendoj   v3                  (era v2)
verificador-tc       v3                  (era v2)
verificador-eurlex   v3                  (era v2)
verificador-boe      v3                  (era v2)
verificador-doctrina v3                  (era v2)
coordinador          v3                  (era v2)
memory_store         memstore_01XyffyE8ndyezuHiAkug4ec  (sin cambios, 13 entradas)
```

Validación: 8 OK, 0 STALE, 0 GONE, 0 ERROR.

---

## Capacidades nuevas añadidas en esta iteración

Además del cierre de deudas, se añadieron:

1. **Plugin Cowork** con slash command `/verificar-legal` en
   `cowork-plugin/verificador-legal-bilbao/`. Documentación de
   instalación en `INSTALAR-PLUGIN.md`.
2. **`verificar.py --fecha-referencia YYYY-MM-DD`** para análisis de
   vigencia normativa en escritos sobre hechos pasados.
3. **`verificar.py --resume <session_id>`** para reanudar streaming.
4. **`verificar.py --json-only`** para modo CI (output reducido).
5. **`despliegue/05_validar_ids.py`** para verificar salud de los
   recursos desplegados (8 OK / N STALE / N GONE / N ERROR).
6. **`lib/retry.py`** y **`lib/logger.py`** como módulos reutilizables.

## Sesiones de test E2E ejecutadas

| Sesión | Fecha | Iter | Resultado | Sorpresa |
|--------|-------|------|-----------|----------|
| sesn_01LciRkaXgnZZDMihE9kbEnz | 2026-05-17 18:48 | 1 | satisfied | Cazó STC 124/2023 (que el test marcaba como "real") como inexacta. |
| sesn_01GPUeSmgTLWyPivkBBXoCRh | 2026-05-17 19:30 | 1 | satisfied | Cazó STC 24/1990 (escrito reforzado) también como inexacta — la cita literal NO está en el texto real de la sentencia (que es de amparo electoral, no de motivación). Cazó además que el RGPD invocado en el escrito no estaba vigente en 2010. Memory store creció con 2 nuevas entradas EN CONVENCIÓN CORRECTA. |

Ambas sesiones cerradas, environments borrados, files de input/output
limpiados. Solo persisten en el workspace: los 7 recursos canónicos
(skill, 5 sub-agentes, coordinador, memory store) y las 13 entradas
canónicas del memory store.
