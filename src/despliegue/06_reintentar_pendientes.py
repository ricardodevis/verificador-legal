"""
Reintenta las citas que quedaron `dudosa_por_infraestructura` en
sesiones anteriores.

Cómo funciona:
  1. Recorre logs/audit-*.jsonl en busca de eventos con
     kind='veredicto_consolidado' y estado='dudosa_por_infraestructura'.
  2. Agrupa por session_id.
  3. Para cada sesión con pendientes, llama a `verificar.py --resume`.
  4. Actualiza el audit log con un evento 'pendientes_reintentados'.

Instalación opcional como cron (cada hora):
    0 * * * * cd ~/Documents/verificador-juris-bilbao && \\
              python3 despliegue/06_reintentar_pendientes.py >> logs/cron.log 2>&1

Instalación opcional como launchd (macOS): ver docs/cron-macos.md.

Uso manual:
    python3 despliegue/06_reintentar_pendientes.py
    python3 despliegue/06_reintentar_pendientes.py --dry-run
    python3 despliegue/06_reintentar_pendientes.py --max-age-hours 48

Exit codes:
  0  todo OK (con o sin pendientes que reintentar)
  2  hubo errores reintentando alguna sesión
"""
from __future__ import annotations
import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parents[1]
LOGS_DIR = ROOT / "logs"
sys.path.insert(0, str(ROOT))
from lib.logger import AuditLog  # noqa: E402


def _parsear_audit(path: Path) -> list[dict]:
    """Lee un audit log JSONL y devuelve los eventos."""
    events = []
    if not path.exists():
        return events
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return events


def _sesion_id_de(path: Path) -> str:
    # logs/audit-sesn_XXX.jsonl → sesn_XXX
    return path.stem.replace("audit-", "")


def _hay_pendientes(events: list[dict]) -> int:
    """Cuenta veredictos dudosa_por_infraestructura en una sesión."""
    n = 0
    for ev in events:
        if (ev.get("kind") in ("veredicto_consolidado", "grader_iteration_end")
                and ev.get("estado") == "dudosa_por_infraestructura"):
            n += 1
        # Compatibilidad: en sesiones nuevas la rama dudosa_por_infraestructura
        # también aparece en eventos del subagent report
        if ev.get("kind") == "subagent_report":
            payload = ev.get("payload") or {}
            if isinstance(payload, dict) and payload.get("estado") == "dudosa_por_infraestructura":
                n += 1
    return n


def _ya_reintentado_recientemente(events: list[dict], cutoff_ts: float) -> bool:
    """Comprueba si ya se reintentó esta sesión recientemente."""
    for ev in events:
        if ev.get("kind") == "pendientes_reintentados":
            try:
                ts = datetime.fromisoformat(ev["ts"].replace("Z", "+00:00")).timestamp()
            except (KeyError, ValueError):
                continue
            if ts > cutoff_ts:
                return True
    return False


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run", action="store_true",
                    help="No relanza nada; solo reporta pendientes.")
    p.add_argument("--max-age-hours", type=int, default=72,
                    help="No reintentar sesiones más antiguas que N horas.")
    p.add_argument("--cooldown-hours", type=int, default=1,
                    help="No reintentar la misma sesión si se reintentó hace menos de N horas.")
    args = p.parse_args()

    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("Error: falta ANTHROPIC_API_KEY en entorno", file=sys.stderr)
        return 1

    if not LOGS_DIR.exists():
        print("No hay logs/ — nada que reintentar.")
        return 0

    now = datetime.now(timezone.utc)
    cutoff_age = now - timedelta(hours=args.max_age_hours)
    cooldown_ts = (now - timedelta(hours=args.cooldown_hours)).timestamp()

    audit_files = sorted(LOGS_DIR.glob("audit-sesn_*.jsonl"))
    print(f"Inspeccionando {len(audit_files)} audit logs...")

    candidatas: list[tuple[str, int, Path]] = []
    for af in audit_files:
        mtime = datetime.fromtimestamp(af.stat().st_mtime, tz=timezone.utc)
        if mtime < cutoff_age:
            continue
        events = _parsear_audit(af)
        n_pendientes = _hay_pendientes(events)
        if n_pendientes == 0:
            continue
        if _ya_reintentado_recientemente(events, cooldown_ts):
            print(f"  [skip cooldown] {_sesion_id_de(af)}: {n_pendientes} pendientes")
            continue
        candidatas.append((_sesion_id_de(af), n_pendientes, af))

    if not candidatas:
        print("Sin sesiones con pendientes en ventana válida.")
        return 0

    print(f"\nSesiones a reintentar: {len(candidatas)}")
    for sid, n, _ in candidatas:
        print(f"  {sid}: {n} citas dudosa_por_infraestructura")

    if args.dry_run:
        print("\n--dry-run: no se relanzaron sesiones.")
        return 0

    errores = 0
    for sid, n, af in candidatas:
        print(f"\n→ reintento {sid} ({n} pendientes)...")
        try:
            res = subprocess.run(
                [sys.executable, str(ROOT / "verificar.py"),
                 "--resume", sid, "--json-only"],
                cwd=str(ROOT),
                capture_output=True, text=True,
                timeout=int(os.environ.get("VERIFICAR_MAX_SECONDS", "1500")) + 60,
            )
            ok = res.returncode == 0
            log = AuditLog(sid, logs_dir=LOGS_DIR)
            log.event("pendientes_reintentados",
                       n_pendientes=n,
                       returncode=res.returncode,
                       stdout_tail=res.stdout[-500:],
                       stderr_tail=res.stderr[-500:])
            if ok:
                print(f"  ✓ ok")
            else:
                errores += 1
                print(f"  ✗ exit code {res.returncode}")
                print(res.stderr[-300:])
        except subprocess.TimeoutExpired:
            errores += 1
            print("  ✗ timeout")
            log = AuditLog(sid, logs_dir=LOGS_DIR)
            log.event("pendientes_reintentados_timeout",
                       n_pendientes=n)

    print(f"\nResumen: {len(candidatas) - errores}/{len(candidatas)} reintentos OK")
    return 2 if errores else 0


if __name__ == "__main__":
    sys.exit(main())
