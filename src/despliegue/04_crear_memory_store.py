"""
Crea el Memory Store del despacho y lo siembra con el README y los
marcadores de directorio.
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
SEED_DIR = ROOT / "memory-seed" / "jurisprudencia"

BETAS = ["managed-agents-2026-04-01"]


@retry_api(max_attempts=4)
def _create_memory_store(client, **kwargs):
    return client.beta.memory_stores.create(**kwargs)


@retry_api(max_attempts=4)
def _create_memory(client, store_id, **kwargs):
    return client.beta.memory_stores.memories.create(store_id, **kwargs)


def cargar_ids() -> dict:
    if IDS_FILE.exists():
        return json.loads(IDS_FILE.read_text(encoding="utf-8"))
    return {}


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

    if "memory_store" in ids:
        print(f"Memory Store ya creado: {ids['memory_store']['id']}")
        return 0

    print("Creando Memory Store 'jurisprudencia-verificada-despacho'...")
    store = _create_memory_store(
        client,
        name="jurisprudencia-verificada-despacho",
        description=(
            "Memoria persistente de jurisprudencia, doctrina y normativa ya "
            "verificada por el despacho. Consulta SIEMPRE este store antes de "
            "delegar una cita a los sub-agentes. Estructura: jurisprudencia/"
            "<tipo>/<año>/<id>.md ; normativa/{estatal,europea}/...; "
            "doctrina/<autor>/."
        ),
        betas=BETAS,
    )
    print(f"  ✓ store.id = {store.id}")

    # Seed README al store
    readme_path = SEED_DIR / "README.md"
    if readme_path.exists():
        print("  → sembrando /README.md...")
        _create_memory(
            client, store.id,
            path="/README.md",
            content=readme_path.read_text(encoding="utf-8"),
            betas=BETAS,
        )

    # Marcadores de directorio (la API trata los memories como flat files
    # pero los paths con / forman jerarquía cuando se listan con depth)
    for marker in ("/jurisprudencia/.keep",
                   "/normativa/.keep",
                   "/doctrina/.keep"):
        try:
            _create_memory(
                client, store.id,
                path=marker,
                content="(placeholder)",
                betas=BETAS,
            )
        except Exception as exc:
            print(f"  ! No se pudo crear {marker}: {exc}")

    ids["memory_store"] = {"id": store.id,
                           "name": "jurisprudencia-verificada-despacho"}
    guardar_ids(ids)
    print(f"  ✓ Guardado en {IDS_FILE}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
