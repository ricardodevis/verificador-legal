"""
Crea el agente coordinador.

Referencia:
  - Los cinco sub-agentes ya creados (multiagent.agents = [ids...])
  - La Skill 'verificador-jurisprudencia-es' ya subida
  - El Memory Store del despacho NO se referencia aquí (los memory
    stores se adjuntan a la sesión, no al agente).

Pre-requisitos: ejecutar antes 01, 03 y 04.
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

PROMPTS_DIR = ROOT / "prompts"
IDS_FILE = ROOT / ".agent-ids.json"

BETAS = ["managed-agents-2026-04-01"]


@retry_api(max_attempts=4)
def _create_agent(client, **kwargs):
    return client.beta.agents.create(**kwargs)


def cargar_ids() -> dict:
    if not IDS_FILE.exists():
        print("Error: .agent-ids.json no existe. Ejecuta 01_crear_subagentes, "
              "03_subir_skill y 04_crear_memory_store antes.", file=sys.stderr)
        sys.exit(1)
    return json.loads(IDS_FILE.read_text(encoding="utf-8"))


def guardar_ids(ids: dict) -> None:
    IDS_FILE.write_text(json.dumps(ids, indent=2, ensure_ascii=False),
                        encoding="utf-8")


def main() -> int:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: falta ANTHROPIC_API_KEY", file=sys.stderr)
        return 1

    client = anthropic.Anthropic(api_key=api_key)
    ids = cargar_ids()

    sub_keys = [
        "verificador-cendoj",
        "verificador-tc",
        "verificador-eurlex",
        "verificador-boe",
        "verificador-doctrina",
    ]
    for k in sub_keys:
        if k not in ids:
            print(f"Error: sub-agente {k} no creado", file=sys.stderr)
            return 1

    if "skill" not in ids:
        print("Error: skill no subida (corre 03_subir_skill.py)",
              file=sys.stderr)
        return 1

    if "coordinador" in ids:
        print("Coordinador ya existe. Borra la entrada de .agent-ids.json "
              "y vuelve a ejecutar si quieres recrearlo.")
        return 0

    print("Creando coordinador...")

    system = (PROMPTS_DIR / "coordinator-system.md").read_text(encoding="utf-8")
    modelo = os.environ.get("DEFAULT_MODEL_OPUS", "claude-opus-4-7")

    agente_coord = _create_agent(
        client,
        name="Coordinador Verificación Jurídica Bilbao.AI",
        description=(
            "Coordina la verificación de citas jurídicas españolas y "
            "europeas delegando en sub-agentes especializados."
        ),
        model=modelo,
        system=system,
        tools=[{"type": "agent_toolset_20260401"}],
        skills=[{
            "type": "custom",
            "skill_id": ids["skill"]["id"],
            "version": ids["skill"].get("version", "latest"),
        }],
        multiagent={
            "type": "coordinator",
            "agents": [ids[k]["id"] for k in sub_keys],
        },
        betas=BETAS,
    )

    ids["coordinador"] = {
        "id": agente_coord.id,
        "version": getattr(agente_coord, "version", 1),
        "model": modelo,
    }
    guardar_ids(ids)
    print(f"  ✓ Coordinador creado: {agente_coord.id}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
