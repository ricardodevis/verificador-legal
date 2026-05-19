# Re-asignación de modelos del Verificador Legal

**Fecha:** 2026-05-18
**Autor:** Ricardo Devis (Bilbao.AI)
**Objetivo:** Bajar coste por verificación sin que se nos cuele una cita falsa.

---

## 1. Mapa actual

| Agente | Modelo actual | Coste relativo (in / out) | Lo que realmente hace |
|---|---|---|---|
| Coordinador | `claude-opus-4-7` | Opus (15 / 75) | Parsea el escrito, despacha citas a sub-agentes, consolida veredictos, escribe memory en convención canónica, decide si una STC dudosa sube como `verificada_por_memoria_con_alerta` o se queda en `dudosa`. |
| verificador-cendoj | `claude-sonnet-4-6` | Sonnet (3 / 15) | Busca en `poderjudicial.es` por nº de recurso, ponente, fecha. Decide si la resolución encontrada coincide con la citada o es otra. Fallback a BOE-A para STS importantes. |
| verificador-tc | `claude-sonnet-4-6` | Sonnet | Busca en `hj.tribunalconstitucional.es`. Detecta atribuciones doctrinales falsas (la STC existe, pero no dice lo que el escrito le atribuye). |
| verificador-eurlex | `claude-sonnet-4-6` | Sonnet | Lookup por CELEX number / nº de asunto. Bilingüe ES/EN/FR. Cross-check eur-lex ↔ curia. |
| verificador-boe | `claude-haiku-4-5-20251001` | Haiku (1 / 5) | Verifica normativa estatal y vigencia histórica con `--fecha-referencia`. Ya es el más barato. |
| verificador-doctrina | `claude-opus-4-7` | Opus | Verifica autoría y revista en Dialnet + catálogos editoriales. Detecta atribuciones doctrinales inventadas con autor real (la rama más sutil del sistema). |

## 2. Lo que sabemos de las dos sesiones E2E

- Sesión `sesn_01LciRkaXgnZZDMihE9kbEnz`: 35K tokens out + ~3M `cache_read` (el cache_read es ~10× más barato que input fresco; aquí está el grueso del coste real).
- Iteración 0 ya `satisfied` por el grader → el sistema NO está rozando el techo de capacidad. Hay margen para bajar modelos sin tocar la rúbrica.
- El coordinador consume mucho cache_read porque arrastra todo el contexto entre rondas. Cada token que metes en su modelo se paga 5× respecto a Sonnet.

## 3. Análisis por rol

### Coordinador — sobredimensionado

Su trabajo, despiezado:

1. **Extraer citas del escrito** → trabajo estructural, plantilla regex+JSON. Sonnet lo hace de sobra.
2. **Routing a sub-agentes** → un `switch` glorificado. Haiku lo haría, pero conviene Sonnet por seguridad de formato.
3. **Consolidar veredictos** → agregación de JSON. Sonnet sobra.
4. **Escribir memory canónica** (`jurisprudencia/sts/2024/...`) → seguir convención. Sonnet sobra.
5. **Decidir si una dudosa sube a verificada_por_memoria_con_alerta** → el único punto donde se podría justificar Opus. Pero ya tienes la rúbrica del Outcome haciendo de segundo par de ojos en un grader aparte.

**Veredicto:** Sonnet 4.6, con el prompt v4 actual (que ya tiene el bloque INVIOLABLE sobre convención de paths). Si en producción detectamos derivas, subimos.

**Ahorro estimado:** ~60% del coste de este agente. Como el coordinador maneja todo el cache_read del sistema, esto solo ya recorta probablemente el **30-35% del coste total** por verificación.

### verificador-cendoj — mantener Sonnet

Necesita razonar sobre coincidencia parcial: misma fecha pero distinto ponente, mismo nº pero recurso casación vs. recurso ordinario. Haiku se equivoca aquí más a menudo de lo que admitimos.

**Veredicto:** Sonnet 4.6. Sin cambios.

### verificador-tc — mantener Sonnet

La detección de "atribuciones doctrinales falsas" (la STC existe, sí, pero no dice lo que le imputan) es de los puntos donde más nos jugamos. Bajar a Haiku es ahorrar 2 céntimos por verificación a cambio de soltar un falso positivo cada 30 escritos. Mala compra.

**Veredicto:** Sonnet 4.6. Sin cambios.

### verificador-eurlex — candidato a Haiku con red de seguridad

CELEX lookup es bastante mecánico. La parte sutil es cuando hay dos sentencias casi homónimas (asunto C-XXX/19 y C-XXX/20). Tres opciones:

- **A**: Mantener Sonnet. Cero riesgo, cero ahorro.
- **B**: Haiku con retry a Sonnet si la confianza del agente <0.8. Requiere meter en el prompt el self-assessment de confianza y un orquestador que escale. Cambio de arquitectura no trivial.
- **C**: Haiku sin red. Riesgo medio-bajo. Solo viable si EUR-Lex es el <15% del corpus del despacho.

**Veredicto:** Sonnet por ahora. Migrar a B solo cuando tengamos métricas de producción reales y veamos que EUR-Lex pesa lo suficiente.

### verificador-boe — mantener Haiku

Vigencia histórica con `--fecha-referencia` requiere razonamiento temporal, pero estructurado (¿qué norma estaba vigente en X fecha?). Haiku 4.5 lo hace bien si el prompt es estricto.

**Veredicto:** Haiku. Sin cambios.

### verificador-doctrina — la pregunta del millón

Es **donde más se nos pueden colar alucinaciones de manual**: autores reales (Pantaleón, Díez-Picazo, Gimbernat) con doctrinas que nunca formularon. El razonamiento semántico fino aquí no es decorativo.

Tres argumentos para bajar a Sonnet:
1. La verificación contra Dialnet es **literal** (existe/no existe el artículo, existe/no existe la revista). El razonamiento difícil ya lo cazó la extracción de la cita.
2. La rúbrica del Outcome puntúa muy duro las falsas verificaciones de doctrina.
3. Sonnet 4.6 está a un palmo de Opus en tareas de matching documental.

Dos argumentos para mantener Opus:
1. Es **la rama menos probada**: solo dos sesiones E2E y ninguna trampa estuvo en doctrina pura.
2. El precio de un falso `verificada` en doctrina es alto: el abogado firma un escrito citando un artículo inexistente y el rival lo encuentra.

**Veredicto:** Sonnet 4.6 **con rúbrica reforzada en el system prompt** (sumar tres ejemplos contraadversariales: autor real + revista real + artículo inventado). Y un flag de configuración para volver a Opus si en producción aparece una alucinación. Es decir: bajamos, pero con freno de mano accesible.

**Ahorro estimado:** ~60% del coste de este agente. Como doctrina aparece en aproximadamente 1 de cada 3 verificaciones, el impacto total es **otro 10-15% sobre el total**.

## 4. Tres estrategias

### Conservadora

| Agente | Antes | Después |
|---|---|---|
| Coordinador | Opus | **Sonnet** |
| Resto | igual | igual |

- **Ahorro estimado:** ~30% por verificación.
- **Riesgo:** Bajo. El coordinador hace trabajo estructural.
- **Trabajo:** Cambiar 1 variable de entorno + revalidar el prompt v4 con Sonnet.

### Mixta (mi recomendación)

| Agente | Antes | Después |
|---|---|---|
| Coordinador | Opus | **Sonnet** |
| Doctrina | Opus | **Sonnet** (con rúbrica reforzada y flag de rollback) |
| Resto | igual | igual |

- **Ahorro estimado:** ~45-55% por verificación.
- **Riesgo:** Medio-bajo. Doctrina necesita un suite de tests adicional (4-5 ejemplos contraadversariales) antes de ir a producción.
- **Trabajo:** 2 variables de entorno + refuerzo del prompt de doctrina + test offline con casos sintéticos.

### Agresiva

| Agente | Antes | Después |
|---|---|---|
| Coordinador | Opus | **Sonnet** |
| Doctrina | Opus | **Sonnet** |
| EUR-Lex | Sonnet | **Haiku con retry a Sonnet** |
| Resto | igual | igual |

- **Ahorro estimado:** ~55-65% por verificación.
- **Riesgo:** Medio. El retry-escalation requiere reentrenar la rúbrica y meter self-assessment de confianza en el prompt de EUR-Lex.
- **Trabajo:** Estrategia mixta + arquitectura de retry escalado en `lib/retry.py` + nuevos tests de comportamiento.

## 5. Lo que NO voy a tocar aunque pueda

- **Haiku para BOE.** Ya está al fondo de la escalera.
- **El grader del Outcome.** Es nuestra red de seguridad. Si recortamos ahí, perdemos la única certificación independiente del sistema.
- **El modelo del PDF de informe** (en `ipip_neo_300_ai_report.py`, fuera del verificador). Otra historia.

## 6. Métrica que necesitamos para validar la decisión

Tras desplegar la estrategia elegida:

1. **5-10 verificaciones reales** sobre escritos del despacho.
2. Comparar el JSON final con la versión Opus (idealmente: A/B paralelo durante una semana).
3. Si **0 falsos `verificada`** sobre citas reales → consolidar.
4. Si **≥1 falso `verificada`** → rollback al modelo anterior en el agente afectado.

Esto es trabajo de operación, no de desarrollo. Lo dejamos preparado con los flags de entorno y se ejecuta cuando arranque el primer despacho cliente.

## 7. Cómo se materializa el cambio

Todos los modelos viven en `.env`:

```env
DEFAULT_MODEL_OPUS=claude-opus-4-7
DEFAULT_MODEL_SONNET=claude-sonnet-4-6
DEFAULT_MODEL_HAIKU=claude-haiku-4-5-20251001

COORDINATOR_MODEL=claude-sonnet-4-6        # antes: claude-opus-4-7
DOCTRINA_MODEL=claude-sonnet-4-6           # antes: claude-opus-4-7
CENDOJ_MODEL=claude-sonnet-4-6
TC_MODEL=claude-sonnet-4-6
EURLEX_MODEL=claude-sonnet-4-6
BOE_MODEL=claude-haiku-4-5-20251001
```

Los scripts `01_crear_subagentes.py` y `02_crear_coordinador.py` ya leen del entorno, así que el cambio es:

1. Editar `.env` del despacho.
2. Re-ejecutar `bootstrap.sh` (idempotente: si los agentes ya existen, los actualiza con `update_agent`).
3. Lanzar un par de verificaciones de prueba.

Si optamos por la mixta, además:

4. Editar `prompts/sub-doctrina-system.md` añadiendo el bloque de 3 ejemplos contraadversariales que prepararé.
5. Re-subir el prompt con `01_crear_subagentes.py --solo doctrina`.

---

## TL;DR

- **Coordinador y doctrina están sobredimensionados.** Bajarlos a Sonnet recorta entre el 45% y el 55% del coste sin tocar la rúbrica.
- **CENDOJ, TC y EUR-Lex se quedan en Sonnet.** Ahí es donde el sistema gana o pierde la confianza del abogado.
- **BOE ya está en Haiku.** Nada que hacer.
- **Mi voto:** Estrategia mixta + rollback flag preparado. Conservadora si quieres ir aún más prudente. Agresiva solo si el primer despacho cliente pide rebaja de tarifa.
