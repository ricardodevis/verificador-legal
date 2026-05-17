# CHANGELOG

Cambios significativos en el proyecto. Formato basado en
[Keep a Changelog](https://keepachangelog.com/), versionado
[SemVer](https://semver.org/).

---

## [Unreleased]

### Roadmap activo

- v1.1 — Integración con vLex/Aranzadi/Tirant vía Vaults de Anthropic.
- v1.2 — Multi-cliente: segregación de memory store por cliente dentro de un mismo despacho.
- v1.3 — Migración a AWS Bedrock AgentCore (Fráncfort).
- v2.0 — Verificación de documentos PDF nativos.

---

## [1.0.0] — 2026-05-17

Primera versión pública open source bajo Apache License 2.0.

### Añadido

#### Sistema de verificación
- Coordinador (Claude Opus 4.7) que orquesta 5 sub-agentes especializados.
- Skill remota `verificador-jurisprudencia-es` con instrucciones, referencias, scripts deterministas y evals.
- Memory store del despacho con persistencia entre asuntos.
- Rúbrica de Outcome de 8 criterios (incluye anti-alucinación, exhaustividad, vigencia normativa).

#### Sub-agentes
- `verificador-cendoj` (Sonnet) — TS, AN, TSJ, AP. Con fallback a BOE-A para STS importantes cuando CENDOJ cae.
- `verificador-tc` (Sonnet) — TC. Detecta atribuciones doctrinales falsas a sentencias existentes.
- `verificador-eurlex` (Sonnet) — TJUE, TGUE, EUR-Lex. Fallback cruzado CURIA ↔ EUR-Lex.
- `verificador-boe` (Haiku) — Normativa estatal + vigencia histórica con `--fecha-referencia`.
- `verificador-doctrina` (Opus) — Dialnet + catálogos editoriales reconocidos.

#### Estados por cita
- `verificada`, `verificada_por_memoria`, `verificada_por_memoria_con_alerta`
- `inexacta`, `no_encontrada`
- `dudosa_por_infraestructura`, `dudosa_por_contenido` (distinción explícita)

#### Resilencia
- Retry-with-backoff exponencial en llamadas a Anthropic API.
- Reintentos escalados (3 s → 8 s → 20 s) en sub-agentes ante 5xx/timeout.
- Fallback de fuente cruzada entre fuentes oficiales.
- Fallback de memoria caducada cuando la fuente cae.
- Job diferido autónomo (`06_reintentar_pendientes.py`) para reintentar citas pendientes.

#### Customización por despacho
- Nombre del despacho.
- Especialidad: penal, civil, mercantil, administrativo, laboral, multidisciplinar.
- Jurisdicciones autonómicas: BOPV, DOGC, BOCM, DOGV, DOG, BOJA, BOA, BORM, DOCM, BON.

#### Plugin Cowork
- `verificador-legal-installer-bilbao` — plugin de mantenimiento con `/instalar-verificador-legal` y modos `--update`, `--validate-only`, `--reinstalar`, `--uninstall`.
- `verificador-legal-<despacho-slug>` — plugin operativo generado en runtime con `/verificar-legal`.
- Modelo de coexistencia "instalador + operativo" claramente documentado.

#### Observabilidad
- Logger JSONL thread-safe (`lib/logger.py`).
- Audit log por sesión en `logs/audit-<session>.jsonl`.
- Script `05_validar_ids.py` para auditar salud del sistema desplegado.

#### Tests
- 12 tests unitarios (extracción, normalización, render).
- 14 tests de comportamiento (mocks de sub-agentes, render, logger, retry).
- 1 escrito de prueba con 8 citas (2 inventadas, 6 reales con diversos casos de inexactitud).
- **26/26 tests offline passing**.

#### Customizador (`customizar.py`)
- Sustituye placeholders en runtime durante instalación.
- Inyecta bloques específicos de especialidad y jurisdicciones en los system prompts.

#### Bootstrap
- `bootstrap.sh` idempotente con validación de entorno, auth, retry-with-backoff y reporte final.

#### Documentación
- Documentación de arquitectura, uso y desarrollo bajo `docs/`.
- Skill instalador con flujo conversacional de 9 pasos guiado.
- Troubleshooting completo en el plugin.

### Sin cambios desde iteraciones internas (0.x)

Las iteraciones 0.1-0.4 fueron desarrollo interno de Bilbao.AI. La
1.0.0 es la consolidación pública de todas ellas. Histórico
interno disponible bajo petición.

### Privacidad y seguridad

- Cero telemetría hacia Bilbao.AI ni hacia terceros.
- API key del despacho vive solo en `.env` local con permisos 600.
- Logs 100% locales.

### Licencia

- Apache License 2.0.

---

## Atribución

Por contribuciones de seguridad o funcionalidad, ver
[`CONTRIBUTING.md`](CONTRIBUTING.md) y
[`SECURITY.md`](SECURITY.md).
