#!/usr/bin/env bash
# Bootstrap del Verificador de Jurisprudencia y Doctrina (Bilbao.AI).
#
# Despliega en el workspace de Anthropic los recursos necesarios para
# que el slash command /verificar-legal funcione:
#   - Skill remota verificador-jurisprudencia-es
#   - 5 sub-agentes (CENDOJ, TC, EUR-Lex, BOE, doctrina)
#   - Memory store del despacho
#   - Coordinador (Opus)
#
# Es IDEMPOTENTE: si algo ya está desplegado, lo respeta y sigue.
# Si algún paso falla, se detiene con mensaje claro (NO reintenta en bucle).
#
# Uso (desde el directorio del proyecto, donde vive este script):
#   bash bootstrap.sh
#
# Pre-requisitos:
#   - python3 >= 3.11
#   - .env con ANTHROPIC_API_KEY válida con permisos de Managed Agents

set -euo pipefail

# --- ubicación + colores -----------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [[ -t 1 ]]; then
    R="$(printf '\033[31m')"; G="$(printf '\033[32m')"
    Y="$(printf '\033[33m')"; B="$(printf '\033[34m')"
    D="$(printf '\033[2m')";  N="$(printf '\033[0m')"
else
    R=""; G=""; Y=""; B=""; D=""; N=""
fi

ok()    { printf "${G}✓${N} %s\n" "$*"; }
warn()  { printf "${Y}!${N} %s\n" "$*"; }
fail()  { printf "${R}✗${N} %s\n" "$*" >&2; exit 1; }
step()  { printf "\n${B}▶${N} %s\n" "$*"; }
note()  { printf "${D}  %s${N}\n" "$*"; }

# --- 1. comprobaciones de entorno --------------------------------------
step "Comprobando entorno"

command -v python3 >/dev/null 2>&1 \
  || fail "python3 no está instalado o no está en PATH"

PYV="$(python3 -c 'import sys; print("%d.%d" % sys.version_info[:2])')"
ok "python3 $PYV detectado"

case "$PYV" in
    3.10|3.11|3.12|3.13|3.14|3.15) ;;
    *) warn "se recomienda Python 3.11+; tienes $PYV — puede funcionar igual" ;;
esac

if [[ ! -f .env ]]; then
    if [[ -f .env.example ]]; then
        fail ".env no existe. Crea uno copiando .env.example y rellena ANTHROPIC_API_KEY:
       cp .env.example .env
       \$EDITOR .env"
    else
        fail ".env no existe y tampoco .env.example. Algo está mal en la copia del proyecto."
    fi
fi
ok ".env presente"

# Cargar .env sin imprimir su contenido
set -a
# shellcheck disable=SC1091
source ./.env
set +a

if [[ -z "${ANTHROPIC_API_KEY:-}" ]]; then
    fail "ANTHROPIC_API_KEY no está definida en .env"
fi
# Validación superficial del formato (sin imprimir la clave)
if [[ ! "$ANTHROPIC_API_KEY" =~ ^sk-ant- ]]; then
    warn "ANTHROPIC_API_KEY no empieza por sk-ant- — comprueba que es correcta"
fi
ok "ANTHROPIC_API_KEY presente (no se mostrará)"

# --- 2. instalar dependencias ------------------------------------------
step "Instalando dependencias Python"

if [[ ! -f requirements.txt ]]; then
    fail "requirements.txt no existe"
fi

# Intentar pip3 normal; si falla por externally-managed, ofrecer flag
if pip3 install -q -r requirements.txt 2>/tmp/bootstrap-pip.err; then
    ok "dependencias instaladas"
else
    if grep -q "externally-managed-environment" /tmp/bootstrap-pip.err 2>/dev/null; then
        warn "entorno Python externally-managed (PEP 668). Usando --break-system-packages"
        pip3 install -q --break-system-packages -r requirements.txt \
          || fail "fallo al instalar dependencias incluso con --break-system-packages"
        ok "dependencias instaladas (--break-system-packages)"
    else
        cat /tmp/bootstrap-pip.err >&2
        fail "fallo al instalar dependencias (ver salida arriba)"
    fi
fi

# --- 3. validación rápida de auth (sin consumir tokens) ----------------
step "Validando autenticación contra api.anthropic.com"

python3 - <<'PY' || fail "auth check falló"
import os, sys
import anthropic
try:
    c = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    list(c.models.list(limit=1))
    print("  ok")
except anthropic.AuthenticationError:
    print("AUTH FAIL: API key inválida", file=sys.stderr); sys.exit(1)
except anthropic.PermissionDeniedError:
    print("PERMISSION FAIL: API key sin permisos suficientes", file=sys.stderr); sys.exit(1)
except Exception as e:
    print(f"ERROR: {type(e).__name__}: {str(e)[:200]}", file=sys.stderr); sys.exit(1)
PY
ok "auth OK"

# --- 4. ejecutar despliegue en orden -----------------------------------
SCRIPTS=(
    "03_subir_skill.py:Skill remota"
    "01_crear_subagentes.py:Sub-agentes (5)"
    "04_crear_memory_store.py:Memory store"
    "02_crear_coordinador.py:Coordinador"
)

for entry in "${SCRIPTS[@]}"; do
    script="${entry%%:*}"
    label="${entry##*:}"
    step "Desplegando: $label  ${D}(despliegue/$script)${N}"
    if ! python3 "despliegue/$script"; then
        fail "fallo en despliegue/$script. Revisa el output. La sesión NO continúa."
    fi
done

# --- 5. validación final ----------------------------------------------
step "Validando todos los IDs registrados"
if ! python3 despliegue/05_validar_ids.py; then
    EXITCODE=$?
    case $EXITCODE in
        2) fail "validación detectó recursos GONE/ERROR. Revisa el output." ;;
        3) warn "validación detectó recursos STALE. El sistema funcionará, pero conviene revisar." ;;
        *) fail "validación falló con código $EXITCODE" ;;
    esac
fi

# --- 6. instrucciones finales ------------------------------------------
cat <<EOF

${G}════════════════════════════════════════════════════════════════════════${N}
${G}  DESPLIEGUE COMPLETO${N}
${G}════════════════════════════════════════════════════════════════════════${N}

El sistema está vivo en tu workspace de Anthropic.
IDs persistidos en ${B}$SCRIPT_DIR/.agent-ids.json${N}

Próximos pasos:

1. Confirma que el plugin de Cowork está instalado:
   - ¿Te aparece /verificar-legal al teclear "/" en Cowork? Si sí, perfecto.
   - Si no, sigue las instrucciones en ${B}INSTALAR-PLUGIN.md${N}.

2. Test rápido sin Cowork:
   ${D}python3 verificar.py pruebas/escrito-de-prueba.md --fecha-referencia 2010-09-01${N}
   (tarda 5-10 min porque hace web fetches reales)

3. Cuando funcione end-to-end:
   - Adjunta un escrito jurídico en Cowork
   - Teclea /verificar-legal
   - El informe llega en logs/informe-<sesion>.md

Para auditar la salud del sistema en cualquier momento:
   ${D}python3 despliegue/05_validar_ids.py${N}

Para reanudar una sesión interrumpida:
   ${D}python3 verificar.py --resume <session_id>${N}

${Y}RECORDATORIO${N}: la API key vive solo en .env (no en git, no en logs,
no en outputs). Rótala cada 90 días en console.anthropic.com.

EOF
