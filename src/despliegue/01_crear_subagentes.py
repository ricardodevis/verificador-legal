"""
Crea los cinco sub-agentes en el workspace de Anthropic.

Guarda los IDs (con `version`) en .agent-ids.json en el directorio raíz
del proyecto. Si un sub-agente ya existe en el fichero, se omite (este
script es idempotente: re-ejecutarlo no crea duplicados).
"""
from __future__ import annotations
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple

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
    if IDS_FILE.exists():
        return json.loads(IDS_FILE.read_text(encoding="utf-8"))
    return {}


def guardar_ids(ids: dict) -> None:
    IDS_FILE.write_text(json.dumps(ids, indent=2, ensure_ascii=False),
                        encoding="utf-8")


def cargar_prompt(nombre: str) -> str:
    return (PROMPTS_DIR / nombre).read_text(encoding="utf-8")


def main() -> int:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: falta ANTHROPIC_API_KEY", file=sys.stderr)
        return 1

    client = anthropic.Anthropic(api_key=api_key)
    ids = cargar_ids()

    modelo_sonnet = os.environ.get("DEFAULT_MODEL_SONNET", "claude-sonnet-4-6")
    modelo_haiku = os.environ.get("DEFAULT_MODEL_HAIKU", "claude-haiku-4-5")
    modelo_opus = os.environ.get("DEFAULT_MODEL_OPUS", "claude-opus-4-7")

    # Toolset por sub-agente.
    toolset_scoped_web = [{
        "type": "agent_toolset_20260401",
        "configs": [
            {"name": "web_search"},
            {"name": "web_fetch"},
            {"name": "write"},
        ],
    }]
    toolset_scoped_fetch_only = [{
        "type": "agent_toolset_20260401",
        "configs": [
            {"name": "web_fetch"},
            {"name": "write"},
        ],
    }]
    toolset_full = [{"type": "agent_toolset_20260401"}]

    definiciones: List[Tuple[str, str, str, list, str]] = [
        ("verificador-cendoj", modelo_sonnet, "sub-cendoj-system.md",
         toolset_scoped_web,
         "Verifica jurisprudencia española contra CENDOJ"),
        ("verificador-tc", modelo_sonnet, "sub-tc-system.md",
         toolset_scoped_web,
         "Verifica jurisprudencia del Tribunal Constitucional"),
        ("verificador-eurlex", modelo_sonnet, "sub-eurlex-system.md",
         toolset_scoped_web,
         "Verifica jurisprudencia y normativa europea (TJUE, EUR-Lex)"),
        ("verificador-boe", modelo_haiku, "sub-boe-system.md",
         toolset_scoped_fetch_only,
         "Verifica normativa estatal española y vigencia temporal"),
        ("verificador-doctrina", modelo_opus, "sub-doctrina-system.md",
         toolset_full,
         "Verifica doctrina académica jurídica"),
    ]

    for nombre, modelo, system_file, tools, descripcion in definiciones:
        if nombre in ids:
            print(f"  → {nombre} ya existe: {ids[nombre]['id']} (omito)")
            continue

        print(f"Creando {nombre}...")
        try:
            agent = _create_agent(
                client,
                name=nombre,
                description=descripcion,
                model=modelo,
                system=cargar_prompt(system_file),
                tools=tools,
                betas=BETAS,
            )
        except Exception as exc:
            print(f"  ✗ Error creando {nombre}: {exc}", file=sys.stderr)
            return 1

        ids[nombre] = {
            "id": agent.id,
            "version": getattr(agent, "version", 1),
            "model": modelo,
        }
        guardar_ids(ids)
        print(f"  ✓ {nombre} → {agent.id} v{ids[nombre]['version']}")

    print(f"\n✓ Sub-agentes registrados en {IDS_FILE}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
