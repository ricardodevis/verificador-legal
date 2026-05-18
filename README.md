# Verificador de Jurisprudencia y Doctrina

> Audita citas jurídicas (jurisprudencia, doctrina y normativa, españolas y europeas) en escritos legales. Detecta sentencias inventadas, atribuciones doctrinales falsas, citas literales inexactas y vigencias normativas no aplicables. **Verifica solo contra fuentes oficiales abiertas.**

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-26%2F26%20passing-brightgreen)](src/pruebas/)
[![Release](https://img.shields.io/badge/release-v1.0.2-blue)](https://github.com/ricardodevis/verificador-legal/releases/latest)
[![Download](https://img.shields.io/badge/⬇_descargar_plugin-v1.0.2-success?style=for-the-badge)](https://github.com/ricardodevis/verificador-legal/releases/latest/download/verificador-legal.plugin)

## ⬇️ Descarga directa

| Artefacto | Enlace | Tamaño |
|---|---|---|
| **Plugin de Cowork** (recomendado) | [verificador-legal.plugin](https://github.com/ricardodevis/verificador-legal/releases/latest/download/verificador-legal.plugin) | 111 KB |
| Hash SHA-256 (verificar integridad) | [verificador-legal.plugin.sha256](https://github.com/ricardodevis/verificador-legal/releases/latest/download/verificador-legal.plugin.sha256) | < 1 KB |
| Manifest (metadatos del release) | [manifest.json](https://github.com/ricardodevis/verificador-legal/releases/latest/download/manifest.json) | 4 KB |
| Código fuente (clonar) | `git clone https://github.com/ricardodevis/verificador-legal.git` | — |

Tras descargar: **doble click en el `.plugin`** → Cowork lo registra → en Cowork teclea `/instalar-verificador-legal`.

---

## Qué es esto

Un sistema multi-agente, construido sobre **Claude Managed Agents** de
Anthropic, que verifica las citas jurídicas que aparecen en un escrito
procesal (recurso, demanda, contestación, dictamen, contrato) contra
las **fuentes oficiales abiertas**:

- **CENDOJ** (Centro de Documentación Judicial del CGPJ) — sentencias del TS, AN, TSJ, AP
- **Tribunal Constitucional** — STC y ATC
- **EUR-Lex** y **CURIA** — jurisprudencia europea (TJUE) y normativa UE
- **BOE** — normativa estatal española y vigencia temporal histórica
- **Dialnet** y catálogos editoriales — doctrina académica
- **Boletines autonómicos** — BOPV, DOGC, BOCM, DOGV, DOG, BOJA, BOA, BORM, DOCM, BON (seleccionables)

Para cada cita devuelve un **veredicto** con explicación, URL canónica
oficial cuando procede, y alertas de vigencia normativa.

**No interpreta jurídicamente. No decide si la cita aplica al caso.
Eso lo decide el letrado.** Esto solo verifica que la cita existe y
que dice lo que se dice que dice.

## Ejemplo de uso

Letrado pega un escrito con esta cita:

> *"La STS 8745/2024, de 31 de febrero, ponente Excmo. Sr. D. Pelayo Imaginario, establece que la indemnización procedente debe calcularse al margen de los baremos administrativos cuando concurran circunstancias excepcionales sobrevenidas con posterioridad al hecho dañoso."*

El verificador devuelve:

> **Estado: `no_encontrada`** — ALUCINACIÓN CONFIRMADA. La sentencia no existe. Tres indicadores convergentes:
> 1. Fecha imposible: el 31 de febrero no existe en el calendario gregoriano.
> 2. Ponente ficticio: "Pelayo Imaginario" no figura en la nómina de magistrados del TS.
> 3. Búsquedas en CENDOJ por ROJ STS 8745/2024 y por ECLI:ES:TS:2024:8745 devuelven "No se ha encontrado ningún resultado".
> La cita literal entrecomillada también es fabricada.
> **Sugerencia**: Si el argumento jurídico de fondo es necesario, buscar en CENDOJ por texto libre con términos 'baremo' + 'circunstancias excepcionales' (jurisdicción Civil) y verificar individualmente.

Aparte de cazar alucinaciones, también:

- Detecta sentencias **reales** a las que se atribuyen holdings falsos.
- Verifica **literalidad** de las citas entrecomilladas contra el texto real.
- Comprueba **vigencia** de normas en la fecha del hecho litigioso (clave para reformas laborales, civil, fiscal).
- Identifica **doctrina inexistente** o mal referenciada.

## Arquitectura en una página

```
                    ┌──────────────────────────────────────┐
                    │  Letrado en Cowork                    │
                    │  /verificar-legal + escrito           │
                    └──────────────┬───────────────────────┘
                                   │
                                   ▼
                    ┌──────────────────────────────────────┐
                    │  verificar.py (cliente local)         │
                    │  - Upload escrito + rúbrica            │
                    │  - Crea sesión con coordinador         │
                    │  - Define outcome con rúbrica          │
                    │  - Stream eventos hasta satisfied      │
                    │  - Descarga informe.md                 │
                    └──────────────┬───────────────────────┘
                                   │
                                   ▼ (api.anthropic.com)
                    ┌──────────────────────────────────────┐
                    │  Coordinador (Opus)                   │
                    │  + Skill 'verificador-jurisprudencia' │
                    │  + Memory store del despacho          │
                    └──────┬──────┬──────┬──────┬──────┬───┘
                           │      │      │      │      │
                  (paralelo, según tipo de cita)
                           │      │      │      │      │
                ┌──────────▼┐   ┌─▼───┐ ┌─▼───┐ ┌▼──┐ ┌▼────────┐
                │ CENDOJ    │   │ TC  │ │EURL.│ │BOE│ │Doctrina │
                │ (Sonnet)  │   │(Son)│ │(Son)│ │(H)│ │(Opus)   │
                └─────┬─────┘   └──┬──┘ └──┬──┘ └─┬─┘ └────┬────┘
                      │            │       │      │        │
                      ▼            ▼       ▼      ▼        ▼
            poderjudicial.es  hj.tc.es  curia/   boe.es  dialnet
                                        eur-lex          + editoriales

                           ▼ (consolidación)
                    ┌──────────────────────────────────────┐
                    │  Grader del Outcome (separado)        │
                    │  Aplica rúbrica al informe            │
                    │  → satisfied / needs_revision         │
                    └──────────────────────────────────────┘
```

Más detalle en [`docs/arquitectura/sistema.md`](docs/arquitectura/sistema.md).

## Estados posibles por cita

| Estado | Significado |
|---|---|
| `verificada` | Existe en fuente oficial, datos coinciden, cita literal localizada. |
| `verificada_por_memoria` | Verificada en asunto anterior del mismo despacho (<90 días). |
| `verificada_por_memoria_con_alerta` | Memoria caducada (>90 días) usada porque la fuente cae temporalmente. Conviene revalidar. |
| `inexacta` | Existe pero la cita literal no aparece o el holding atribuido no coincide. |
| `no_encontrada` | No aparece en bases oficiales. Riesgo alto de alucinación. |
| `dudosa_por_infraestructura` | La fuente oficial no respondía. El sistema no sabe si la cita es buena. Reintentar con `--resume`. |
| `dudosa_por_contenido` | La fuente respondió pero hay ambigüedad real (revisión humana recomendada). |

Más detalle en [`docs/arquitectura/fallback-y-estados.md`](docs/arquitectura/fallback-y-estados.md).

## Instalación rápida

### Opción A — Para usuarios finales (despachos jurídicos)

Descarga el plugin de Cowork desde la última [release](https://github.com/ricardodevis/verificador-legal/releases/latest):

```
verificador-legal.plugin
```

Doble click → Cowork lo registra → `/instalar-verificador-legal` → conversación de 10 min.

Más detalle en [`docs/uso/instalacion.md`](docs/uso/instalacion.md).

### Opción B — Para desarrolladores

```bash
git clone https://github.com/ricardodevis/verificador-legal.git
cd verificador-legal/src
cp .env.example .env
# editar .env con ANTHROPIC_API_KEY
pip install -r requirements.txt
bash bootstrap.sh
```

Tests offline (sin tocar la red ni la API):

```bash
pytest pruebas/ -v
# 26/26 passed in ~0.25 s
```

Test E2E (consume tokens reales):

```bash
python verificar.py pruebas/escrito-de-prueba.md --fecha-referencia 2010-09-01
```

Más detalle en [`docs/desarrollo/setup-dev.md`](docs/desarrollo/setup-dev.md).

## Requisitos

- macOS o Linux
- Python 3.10+
- Cuenta de Anthropic con permisos de Managed Agents (beta `managed-agents-2026-04-01`)
- Conexión a Internet (`api.anthropic.com` + fuentes oficiales)
- **Coste estimado**: 5-10 USD por verificación E2E con caching agresivo

Cowork (escritorio) se necesita solo para el slash command `/verificar-legal`. Sin Cowork también funciona — se invoca con `python verificar.py <escrito>` desde terminal.

## Customización por despacho

El plugin instalador permite configurar:

- **Nombre del despacho**: aparece en los IDs de agentes y en el plugin operativo.
- **Especialidad principal**: penal, civil, mercantil, administrativo, laboral, multidisciplinar. Ajusta tonalidad y prioridades de los sub-agentes.
- **Jurisdicciones autonómicas**: habilita boletines oficiales adicionales (BOPV, DOGC, BOCM, DOGV, DOG, BOJA, BOA, BORM, DOCM, BON).

Más detalle en [`docs/uso/jurisdicciones.md`](docs/uso/jurisdicciones.md).

## Privacidad

- **Cero telemetría** hacia Bilbao.AI ni hacia terceros.
- La API key vive **solo en el `.env` local del despacho** (`chmod 600`), nunca en logs ni outputs.
- Los escritos se suben a la Files API de Anthropic durante la verificación. Su retención y borrado se rigen por la política de Anthropic.
- Los logs de auditoría son **locales**, JSONL por sesión en `logs/audit-*.jsonl`.

## Coste por verificación

| Concepto | Estimado |
|---|---|
| Despliegue inicial (una vez) | 1-2 USD |
| Verificación E2E sin caching | 6-10 USD |
| Verificación E2E con caching (citas conocidas) | 1-3 USD |
| Memory store (citas reutilizadas) | gratis |

Coste real depende del número de citas, complejidad y políticas de pricing vigentes de Anthropic. El sistema usa **prompt caching** agresivo: las verificaciones posteriores sobre el mismo despacho son sustancialmente más baratas.

## Estado del proyecto

- **Versión**: 1.0.0 (mayo 2026)
- **Tests offline**: 26/26 passing
- **Tests E2E**: 2 sesiones documentadas (8 citas detectadas, clasificación correcta)
- **En producción**: 1 despliegue piloto (Bilbao.AI)

## Roadmap

Próximas líneas de trabajo (issues etiquetados como `roadmap`):

- **v1.1** — Integración con vLex/Aranzadi/Tirant vía Vaults de Anthropic (para despachos con suscripción comercial).
- **v1.2** — Multi-cliente: segregación de memory store por cliente dentro de un mismo despacho.
- **v1.3** — Migración a AWS Bedrock AgentCore (Fráncfort) para clientes con requisitos de soberanía de datos UE.
- **v2.0** — Verificación de documentos PDF nativos (sin paso intermedio markdown).

Ver [`CHANGELOG.md`](CHANGELOG.md) para histórico completo.

## Contribuir

Contribuciones bienvenidas. Ver [`CONTRIBUTING.md`](CONTRIBUTING.md).

Para reportar vulnerabilidades de seguridad, ver [`SECURITY.md`](SECURITY.md).

## Licencia

Apache License 2.0. Ver [`LICENSE`](LICENSE).

El uso comercial está **explícitamente permitido**. El negocio de Bilbao.AI alrededor de este software es **servicio**: despliegue gestionado, soporte profesional, formación y actualizaciones premium. Si necesitas eso, contacta `info@bilbao.ai`.

## Autor y contacto

**Ricardo Devis** — `ricardo@bilbao.ai`
**Bilbao AI S.L.** — CIF B-13759758 — Bilbao
`info@bilbao.ai` (soporte y comercial)

## Agradecimientos

- [Anthropic](https://anthropic.com) por el modelo Claude, la API Managed Agents y el framework de skills/plugins.
- [CENDOJ](https://www.poderjudicial.es/search/indexAN.jsp), [Tribunal Constitucional](https://hj.tribunalconstitucional.es), [EUR-Lex](https://eur-lex.europa.eu), [CURIA](https://curia.europa.eu), [BOE](https://www.boe.es) y [Dialnet](https://dialnet.unirioja.es) por sostener fuentes oficiales abiertas y accesibles.
- A los letrados que probaron versiones beta y nos hicieron mejorarlo.
