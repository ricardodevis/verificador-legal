"""
Valida que todos los recursos listados en .agent-ids.json siguen vivos
en el workspace de Anthropic.

Hace `retrieve` de cada ID con retry-with-backoff y reporta:
  - OK: existe y responde
  - GONE: el ID no existe (404)
  - ERROR: otra cosa
  - STALE: existe pero la versión registrada no coincide con la última
    (skill o agent updateado fuera del proceso)

Uso:
    python despliegue/05_validar_ids.py

Exit codes:
  0  todos OK
  2  hay GONE/ERROR
  3  hay STALE (existen pero versión desactualizada)
"""
from __future__ import annotations
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
import anthropic

load_dotenv()

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from lib.retry import retry_api  # noqa: E402

IDS_FILE = ROOT / ".agent-ids.json"
BETAS_MA = ["managed-agents-2026-04-01"]
BETAS_SK = ["skills-2025-10-02"]


@retry_api(max_attempts=3)
def _retrieve_agent(c, aid, betas=BETAS_MA):
    return c.beta.agents.retrieve(aid, betas=betas)


@retry_api(max_attempts=3)
def _retrieve_skill(c, sid, betas=BETAS_SK):
    return c.beta.skills.retrieve(sid, betas=betas)


@retry_api(max_attempts=3)
def _retrieve_memstore(c, mid, betas=BETAS_MA):
    return c.beta.memory_stores.retrieve(mid, betas=betas)


def main() -> int:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: falta ANTHROPIC_API_KEY", file=sys.stderr)
        return 1
    if not IDS_FILE.exists():
        print("Error: .agent-ids.json no existe", file=sys.stderr)
        return 1

    c = anthropic.Anthropic(api_key=api_key)
    ids = json.loads(IDS_FILE.read_text(encoding="utf-8"))

    fails_gone: list[str] = []
    fails_error: list[tuple[str, str]] = []
    stale: list[str] = []
    oks: list[str] = []

    def check_agent(label: str, info: dict) -> None:
        try:
            obj = _retrieve_agent(c, info["id"])
            registered = str(info.get("version", "?"))
            current = str(getattr(obj, "version", "?"))
            if registered != current:
                stale.append(f"{label}: registered v{registered} → workspace v{current}")
            else:
                oks.append(f"{label} → {info['id']} v{current}")
        except anthropic.NotFoundError:
            fails_gone.append(f"{label} ({info['id']})")
        except Exception as exc:
            fails_error.append((label, str(exc)))

    # Sub-agentes
    for name in ("verificador-cendoj", "verificador-tc",
                  "verificador-eurlex", "verificador-boe",
                  "verificador-doctrina"):
        if name in ids:
            check_agent(name, ids[name])
        else:
            fails_gone.append(f"{name} (no registrado)")

    # Coordinador
    if "coordinador" in ids:
        check_agent("coordinador", ids["coordinador"])
    else:
        fails_gone.append("coordinador (no registrado)")

    # Skill
    if "skill" in ids:
        info = ids["skill"]
        try:
            sk = _retrieve_skill(c, info["id"])
            latest = str(getattr(sk, "latest_version", "?"))
            registered = str(info.get("version", "?"))
            if registered != latest:
                stale.append(
                    f"skill: registered v{registered} → latest v{latest}"
                )
            else:
                oks.append(f"skill → {info['id']} v{latest}")
        except anthropic.NotFoundError:
            fails_gone.append(f"skill ({info['id']})")
        except Exception as exc:
            fails_error.append(("skill", str(exc)))

    # Memory store
    if "memory_store" in ids:
        info = ids["memory_store"]
        try:
            _retrieve_memstore(c, info["id"])
            oks.append(f"memory_store → {info['id']}")
        except anthropic.NotFoundError:
            fails_gone.append(f"memory_store ({info['id']})")
        except Exception as exc:
            fails_error.append(("memory_store", str(exc)))

    print("=== Validación de IDs ===")
    for ok in oks:
        print(f"  OK    {ok}")
    for s in stale:
        print(f"  STALE {s}")
    for g in fails_gone:
        print(f"  GONE  {g}")
    for label, msg in fails_error:
        print(f"  ERROR {label}: {msg}")

    print(f"\nResumen: {len(oks)} OK, {len(stale)} STALE, "
          f"{len(fails_gone)} GONE, {len(fails_error)} ERROR")

    if fails_gone or fails_error:
        return 2
    if stale:
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
