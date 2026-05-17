# Troubleshooting del instalador

Esta tabla resume los errores más comunes durante la instalación,
su causa probable y la solución concreta a mostrar al usuario.

## Errores de entorno

| Síntoma | Causa | Solución |
|---|---|---|
| `python3 --version` falla | Python no instalado | macOS: `brew install python@3.11`. Linux: `sudo apt install python3.11`. |
| Versión Python < 3.10 | OS antiguo | Actualizar sistema o instalar Python via pyenv. |
| `pip3` no encontrado | Python sin pip | `python3 -m ensurepip --upgrade`. |
| `command not found: brew` (macOS) | Homebrew no instalado | Instalar Homebrew desde https://brew.sh, luego retry. |

## Errores de autenticación

| Síntoma | Causa | Solución |
|---|---|---|
| `AuthenticationError 401` | API key inválida o tipo equivocado | Verificar en console.anthropic.com. La key debe ser de tipo "API key" no "Admin key". |
| `PermissionDeniedError 403` con `managed_agents` | API key sin permisos de beta | Acceder a console.anthropic.com → Settings → Beta features → activar Managed Agents. |
| `models.list` devuelve lista vacía | Workspace sin modelos activos | Activar modelos en console.anthropic.com → Models. |

## Errores de despliegue

| Síntoma | Causa | Solución |
|---|---|---|
| `SKILL.md file must be exactly in the top-level folder` | Bug histórico, no debería ocurrir si usas v4 | Confirma que el system-template tiene SKILL.md en la raíz de `skill/verificador-jurisprudencia-es/`. |
| `Agent has invalid configuration: skill_id ... version ... not found` | Skill version mismatch | Re-ejecutar `03_subir_skill.py` para obtener la versión actual; actualizar `.agent-ids.json`. |
| Bootstrap se cuelga >30 min | Conexión lenta o rate-limit | Cancelar (Ctrl+C); el script es idempotente, retry. |
| `pip install` falla con `externally-managed-environment` | macOS/Linux con PEP 668 | El bootstrap usa `--break-system-packages` automáticamente. Si falla, instalar `python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`. |

## Errores de plugin Cowork

| Síntoma | Causa | Solución |
|---|---|---|
| `/verificar-legal` no aparece tras instalación | Cowork no reiniciado | Cerrar Cowork completamente (no minimizar) y abrir de nuevo. |
| Plugin instalado pero da error al ejecutar | Ruta `PROJECT_HOME` mal sustituida | Comprobar `cat ~/.config/claude-cowork/plugins/verificador-legal-*/commands/verificar-legal.md` — el placeholder `{{PROJECT_HOME}}` debe estar resuelto. |
| Slash command lanza pero no encuentra `verificar.py` | `VERIFICADOR_JURIS_HOME` o ruta del plugin mal | Editar `.env` del proyecto o exportar `VERIFICADOR_JURIS_HOME` en `~/.zshrc`. |

## Errores de filesystem

| Síntoma | Causa | Solución |
|---|---|---|
| `Permission denied` al escribir en `~/Documents/` | Permisos restrictivos | `chmod 755 ~/Documents/`. |
| Directorio destino ya existe con contenido | Instalación previa o conflicto | Pedir confirmación al usuario antes de sobreescribir; ofrecer renombrar. |
| `~/.config/claude-cowork/plugins/` no existe | Cowork nunca ejecutado | El installer lo crea (`mkdir -p`). Si falla por permisos, pedir al usuario que ejecute Cowork al menos una vez. |

## Errores durante el test E2E

| Síntoma | Causa | Solución |
|---|---|---|
| Test E2E timeout | Coordinador atascado o web fetches lentos | Recuperar `session_id` del log; ejecutar `python3 verificar.py --resume <sid>` manualmente. |
| Grader devuelve `needs_revision` indefinidamente | Rúbrica vs informe en conflicto | Revisar el informe en `logs/`. Si parece correcto pero el grader insiste, abrir ticket. |
| Grader devuelve `failed` | Rúbrica no aplicable al escrito | El escrito de prueba ya está calibrado; si falla aquí, hay un problema en la rúbrica o en los prompts. Re-ejecutar `bash bootstrap.sh` puede solucionarlo. |

## Cuando nada funciona

1. Capturar `logs/cron.log`, `audit-*.jsonl` más reciente, y el
   output completo del bootstrap.
2. Empaquetar (sin la API key):
   ```bash
   cd ~/Documents/verificador-juris-bilbao
   tar -czf debug-bundle.tgz logs/ .agent-ids.json prompts/
   ```
3. Abrir ticket con Bilbao.AI adjuntando el bundle.
