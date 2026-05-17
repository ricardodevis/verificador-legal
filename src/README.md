# Verificador de Jurisprudencia y Doctrina (España + UE)

Sistema de auditoría de citas jurídicas españolas y europeas para
escritos legales del despacho cliente. Construido sobre Claude
Managed Agents (beta `managed-agents-2026-04-01`).

## Qué hace

Recibe un escrito jurídico (recurso, dictamen, demanda, contrato…),
extrae cada referencia jurisprudencial, doctrinal o normativa, y la
verifica contra fuentes oficiales abiertas: CENDOJ, Tribunal
Constitucional, EUR-Lex/CURIA, BOE y Dialnet. Devuelve un informe
markdown con estado por cita (`verificada`, `verificada_por_memoria`,
`inexacta`, `no_encontrada`, `dudosa`), URL canónica oficial cuando
procede, y alertas de vigencia normativa.

NO modifica el texto original. NO emite juicios sobre aplicabilidad
jurídica. NO usa bases comerciales (vLex, Aranzadi, Tirant) en esta
versión.

## Componentes desplegados

- **Skill** `verificador-jurisprudencia-es`: instrucciones procedurales
  con referencias, scripts deterministas y evals.
- **Coordinador** (modelo Opus): orquesta el flujo y produce el
  informe. Recibe la Skill y consume el Memory Store del despacho.
- **Cinco sub-agentes** especializados, ejecutables en paralelo:
  - `verificador-cendoj` (Sonnet) — Tribunal Supremo, AN, TSJ, AP
  - `verificador-tc` (Sonnet) — Tribunal Constitucional
  - `verificador-eurlex` (Sonnet) — TJUE, Reglamentos, Directivas
  - `verificador-boe` (Haiku) — normativa estatal + vigencia
  - `verificador-doctrina` (Opus) — bibliografía académica
- **Rúbrica de Outcome**: contrato de calidad que el grader del
  harness aplica al informe en cada iteración.
- **Memory Store** `jurisprudencia-verificada-despacho`: memoria
  persistente del despacho. Se consulta antes de delegar para
  reutilizar verificaciones previas.

## Instalación

```bash
cp .env.example .env          # rellenar API key + workspace id
pip install -r requirements.txt
```

## Despliegue (primera vez)

Ejecutar EN ESTE ORDEN:

```bash
python despliegue/03_subir_skill.py          # crea la skill
python despliegue/01_crear_subagentes.py     # cinco sub-agentes
python despliegue/04_crear_memory_store.py   # memory store
python despliegue/02_crear_coordinador.py    # coordinador con todo
```

Los IDs resultantes quedan en `.agent-ids.json` (NO subir a git).

## Uso

```bash
python verificar.py ruta/al/escrito.md
```

El informe se guarda en `logs/informe-<session_id>.md`.

## Tests

### Tests unitarios (offline, en local)

Validan extracción, normalización y renderizado sin tocar la API:

```bash
pytest pruebas/test_unitarios.py -v
```

### Test end-to-end (requiere despliegue completo + credenciales)

```bash
python pruebas/test_e2e.py
```

Lanza `verificar.py` contra `pruebas/escrito-de-prueba.md` y comprueba
que las cuatro citas críticas (dos reales, dos inventadas) se
clasifican correctamente.

## Mantenimiento

- Actualizar las URLs base de las fuentes oficiales en
  `skill/verificador-jurisprudencia-es/references/bases-oficiales.md`
  si cambian.
- Revalidación periódica del Memory Store: cada 180 días.
- Re-subir la Skill con `python despliegue/03_subir_skill.py` si se
  modifican sus ficheros. Recordar borrar la entrada `skill` de
  `.agent-ids.json` antes para forzar recreación.
- Para regenerar un sub-agente: borrar su entrada de `.agent-ids.json`
  y re-ejecutar `01_crear_subagentes.py`.

## Reglas inviolables (recordatorio)

- No usar bases comerciales sin contratar credenciales con Vault.
- No marcar como verificada ninguna cita basándose en agregadores o
  espejos. Solo dominios oficiales autorizados.
- Verificación de citas literales: descargar texto completo y
  comprobar coincidencia.
- Toda decisión final corresponde al letrado, no al sistema.

## Migración futura a AWS Bedrock AgentCore (Fráncfort)

Esta primera versión va contra `api.anthropic.com`. La migración a
Bedrock AgentCore (despliegue en región europea, datos UE) será un
encargo independiente.

## Contacto

Bilbao.AI — Ricardo Devis
