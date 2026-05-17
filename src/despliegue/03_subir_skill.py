"""
Sube la Skill 'verificador-jurisprudencia-es' al workspace de Anthropic.

Usa el método `client.beta.skills.create(...)` con `files_from_dir`,
que recorre el directorio del skill y empaqueta los ficheros.

Guarda el `skill_id` devuelto en `.agent-ids.json` para que el
coordinador pueda referenciarlo después.
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

SKILL_DIR = ROOT / "skill" / "verificador-jurisprudencia-es"
IDS_FILE = ROOT / ".agent-ids.json"

BETAS_SKILLS = ["skills-2025-10-02"]


@retry_api(max_attempts=4)
def _create_skill(client, **kwargs):
    return client.beta.skills.create(**kwargs)


def cargar_ids() -> dict:
    if IDS_FILE.exists():
        return json.loads(IDS_FILE.read_text(encoding="utf-8"))
    return {}


def guardar_ids(ids: dict) -> None:
    IDS_FILE.write_text(json.dumps(ids, indent=2, ensure_ascii=False),
                        encoding="utf-8")


def main() -> int:
    if not SKILL_DIR.exists():
        print(f"Error: directorio del skill no existe: {SKILL_DIR}",
              file=sys.stderr)
        return 1

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: falta ANTHROPIC_API_KEY en entorno (revisa .env)",
              file=sys.stderr)
        return 1

    client = anthropic.Anthropic(api_key=api_key)

    ids = cargar_ids()
    if "skill" in ids:
        print(f"Skill ya existe: {ids['skill']['id']}. "
              f"Para recrearla, borra la entrada de .agent-ids.json.")
        return 0

    print(f"Empaquetando y subiendo skill desde {SKILL_DIR}...")

    # IMPORTANTE: la API de Skills exige que TODOS los ficheros estén bajo
    # un mismo directorio top-level. SKILL.md debe estar en la raíz de ese
    # directorio. Por eso prefijamos cada path con el nombre del skill.
    skill_name = SKILL_DIR.name
    files_payload = []
    for p in sorted(SKILL_DIR.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(SKILL_DIR)
        # Filtrar artefactos de Python
        if "__pycache__" in rel.parts or rel.suffix == ".pyc":
            continue
        files_payload.append((f"{skill_name}/{rel}", p.read_bytes()))

    skill = _create_skill(
        client,
        display_title="Verificador de Jurisprudencia y Doctrina (ES + UE)",
        files=files_payload,
        betas=BETAS_SKILLS,
    )

    skill_id = getattr(skill, "id", None)
    # En la API de Skills la versión es un snowflake/timestamp string,
    # NO un entero. Usamos `latest_version` si está presente.
    skill_version = (getattr(skill, "latest_version", None)
                     or getattr(skill, "version", None)
                     or "latest")
    if not skill_id:
        print(f"  ✗ La API no devolvió skill_id: {skill}", file=sys.stderr)
        return 1

    print(f"  ✓ Skill subida. id={skill_id} version={skill_version}")

    ids["skill"] = {"id": skill_id, "version": str(skill_version),
                    "name": "verificador-jurisprudencia-es"}
    guardar_ids(ids)
    print(f"  ✓ Guardado en {IDS_FILE}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
