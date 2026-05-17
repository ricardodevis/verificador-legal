# Cómo instalar `/verificar-legal` en tu Cowork

Esta guía explica cómo activar el slash command `/verificar-legal` en
Cowork para que dispare el sistema de verificación de citas jurídicas.

## Resumen mental del flujo

```
Tú: /verificar-legal [adjunta escrito.docx]
   ↓
Cowork (con plugin instalado) localiza el proyecto
   ↓
Ejecuta: python verificar.py pruebas/escrito.docx
   ↓
verificar.py llama a Anthropic API:
   - sube fichero + rúbrica
   - crea environment + sesión con coordinador y memory store
   - lanza user.define_outcome
   - stream de eventos hasta grader=satisfied
   ↓
Recupera /mnt/session/outputs/informe.md y te lo muestra
```

Hay **dos piezas** que tienen que estar bien:

1. El **sistema desplegado** (skill + 5 sub-agentes + memory store +
   coordinador) en el workspace de Anthropic.
2. El **plugin de Cowork** que añade el slash command.

## Paso 0 — Prerrequisitos en tu máquina

- macOS o Linux. Python 3.11+ (`python3 --version`).
- Cowork instalado.
- Tu API key de Anthropic con permisos sobre Managed Agents
  (beta `managed-agents-2026-04-01`).

## Paso 1 — Despliega el sistema (una sola vez)

Si todavía NO has desplegado el sistema en Anthropic, **lo más rápido
es usar `bootstrap.sh`**:

```bash
# 1.1 Descomprime el proyecto donde te apetezca; convención:
tar -xzf verificador-juris-bilbao.tgz -C ~/Documents/
cd ~/Documents/verificador-juris-bilbao

# 1.2 Configura el entorno
cp .env.example .env
# editar .env con: ANTHROPIC_API_KEY=sk-ant-...
# (NO subir .env a git — ya está en .gitignore)

# 1.3 Ejecuta el bootstrap (atajo recomendado)
bash bootstrap.sh
```

El bootstrap es idempotente: comprueba prerrequisitos, instala
dependencias, valida la auth, ejecuta los 4 scripts de despliegue
en orden, y termina con `05_validar_ids.py` para confirmar salud.
Si algo falla, se detiene con mensaje claro (NO reintenta en bucle).

### Hacerlo manualmente si prefieres control fino

```bash
pip install -r requirements.txt
python3 -m pytest pruebas/test_unitarios.py pruebas/test_comportamiento.py -v
python despliegue/03_subir_skill.py
python despliegue/01_crear_subagentes.py
python despliegue/04_crear_memory_store.py
python despliegue/02_crear_coordinador.py
python despliegue/05_validar_ids.py
```

Si tu sistema YA está desplegado (es tu caso si Cowork ya hizo el
despliegue inicial), salta al paso 2.

Para confirmar que sigue vivo:

```bash
cd ~/Documents/verificador-juris-bilbao
python despliegue/05_validar_ids.py
# Debe imprimir 8 OK, 0 STALE, 0 GONE, 0 ERROR
```

## Paso 2 — Instala el plugin de Cowork

El plugin vive en `cowork-plugin/verificador-legal-bilbao/` dentro del
proyecto.

### Opción A — Instalación directa (recomendada)

Cowork detecta plugins en `~/.config/claude-cowork/plugins/`:

```bash
mkdir -p ~/.config/claude-cowork/plugins
cp -r cowork-plugin/verificador-legal-bilbao ~/.config/claude-cowork/plugins/
```

Reinicia Cowork. Comprueba que aparece `/verificar-legal` al teclear
`/` en el chat.

### Opción B — Empaquetar como .plugin para distribución

Si quieres distribuirlo al equipo del despacho:

```bash
cd cowork-plugin
zip -r verificador-legal-bilbao.plugin verificador-legal-bilbao/
# Compartes verificador-legal-bilbao.plugin
# Cada compañero hace doble clic en el .plugin para instalarlo
```

## Paso 3 — Configura la ruta del proyecto (importante)

El plugin necesita saber dónde vive el proyecto en tu máquina. Tienes
dos opciones:

**Opción A — Convención (más simple)**: deja el proyecto en
`~/Documents/verificador-juris-bilbao/`. El plugin lo busca ahí por
defecto.

**Opción B — Variable de entorno**: si lo tienes en otro sitio, añade
a tu `~/.zshrc` o `~/.bashrc`:

```bash
export VERIFICADOR_JURIS_HOME="$HOME/code/verificador-juris-bilbao"
```

Reinicia Cowork o abre una terminal nueva tras editar el shell rc.

## Paso 4 — Primer uso

Abre Cowork. Adjunta un escrito jurídico (`.docx`, `.pdf`, `.md`,
`.txt`) en el chat y escribe:

```
/verificar-legal
```

Cowork debería responder algo del estilo:

> Detecto `recurso.docx` adjunto. Lo copio a `pruebas/recurso.docx`
> en el proyecto y lanzo el verificador. Esto va a tardar entre 3 y 10
> minutos porque los sub-agentes hacen web fetches reales contra
> CENDOJ, BOE, TC y EUR-Lex. Te aviso al terminar.

Al terminar, te muestra el informe markdown completo con resumen
ejecutivo, tabla por cita, anexo de riesgo (si hay citas
problemáticas) y anexo de vigencia (si hay alertas normativas).

## Paso 5 — Otros usos del comando

```
/verificar-legal pruebas/escrito-de-prueba.md
/verificar-legal --fecha-referencia 2010-09-01 demanda-despido.docx
/verificar-legal --resume sesn_01XYZ...    # reanuda sesión interrumpida
```

## Troubleshooting

| Síntoma | Causa probable | Solución |
|---|---|---|
| `/verificar-legal` no aparece | Plugin no instalado o Cowork no reiniciado | Repite Paso 2 + reinicia Cowork |
| "no encuentro el proyecto" | Ruta no es la convención y `VERIFICADOR_JURIS_HOME` no está exportada | Define la variable o mueve el proyecto a `~/Documents/` |
| "falta ANTHROPIC_API_KEY" | `.env` no creado | Copia `.env.example` a `.env` y rellena la key |
| "error 401 invalid api key" | API key revocada o sin permiso de Managed Agents | Crea nueva key en console.anthropic.com con scope de beta |
| Test E2E dice `failed` | Rúbrica no cuadra con la tarea; el documento no es jurídico | Comprueba que el escrito contiene citas; mira el `audit-<sid>.jsonl` |
| `STALE` en `validate_ids.py` | Algo se modificó fuera del flujo | Re-ejecuta los scripts de despliegue afectados |

## Coste por verificación

Una verificación E2E típica con el escrito de prueba (~7 citas) cuesta
aproximadamente **5-10 USD** en tarifas vigentes (mayo 2026). El
prompt caching reduce drásticamente el coste en verificaciones
posteriores sobre escritos similares.

## Rotación de la API key

La API key de Anthropic vive solo en `~/Documents/verificador-juris-bilbao/.env`,
nunca se sube a git (`.gitignore` la excluye), nunca se imprime en
logs ni en outputs del informe. Aun así, conviene rotarla cada 90
días en `console.anthropic.com` y actualizar el `.env`.
