"""
Test end-to-end. Lanza verificar.py contra el escrito de prueba y
comprueba que el informe identifica correctamente las cuatro citas.

PRE-REQUISITOS para ejecutarlo:
  - .env con ANTHROPIC_API_KEY y ANTHROPIC_WORKSPACE_ID
  - .agent-ids.json con coordinador + sub-agentes + skill + memory_store
  - Conectividad a api.anthropic.com, poderjudicial.es, boe.es,
    eur-lex.europa.eu, hj.tribunalconstitucional.es

NO ejecutar contra documentos reales del despacho. Solo para este
fichero de prueba.
"""
from __future__ import annotations
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ESCRITO = ROOT / "pruebas" / "escrito-de-prueba.md"
LOGS_DIR = ROOT / "logs"


def main() -> int:
    print(f"Lanzando verificar.py contra {ESCRITO.name}...")
    res = subprocess.run(
        [sys.executable, str(ROOT / "verificar.py"), str(ESCRITO)],
        capture_output=True, text=True, cwd=str(ROOT),
    )
    print("--- STDOUT ---")
    print(res.stdout)
    if res.stderr:
        print("--- STDERR ---")
        print(res.stderr)
    if res.returncode not in (0, 2):
        print(f"FAIL: verificar.py salió con código {res.returncode}")
        return 1

    informes = sorted(LOGS_DIR.glob("informe-*.md"),
                       key=lambda p: p.stat().st_mtime, reverse=True)
    if not informes:
        print("FAIL: no se generó ningún informe")
        return 1

    informe = informes[0].read_text(encoding="utf-8")
    print(f"\nInforme analizado: {informes[0]}\n")

    fails: list[str] = []
    lower = informe.lower()

    # 1. STC 124/2023 debe aparecer y estar verificada
    if "STC 124/2023" not in informe:
        fails.append("STC 124/2023 no aparece en el informe")
    else:
        bloque = informe[informe.index("STC 124/2023"):
                          informe.index("STC 124/2023") + 400]
        if "verificada" not in bloque.lower():
            fails.append("STC 124/2023 no marcada como verificada")

    # 2. STS 8745/2024 debe ser no_encontrada (fecha imposible 31-feb)
    if "8745/2024" not in informe:
        fails.append("STS 8745/2024 (inventada) no detectada")
    elif "no_encontrada" not in lower:
        fails.append("ninguna cita marcada como no_encontrada")

    # 3. Reglamento UE 2016/679
    if "2016/679" not in informe:
        fails.append("Reglamento UE 2016/679 no detectado")

    # 4. STJUE C-311/18
    if "C-311/18" not in informe:
        fails.append("STJUE C-311/18 no detectada")

    # 5. MARTÍNEZ CALCERRADA con obra de 2027 — debe ser no_encontrada
    if ("MARTÍNEZ" not in informe.upper()
            and "CALCERRADA" not in informe.upper()):
        fails.append("Doctrina inventada no detectada")

    if fails:
        print("✗ TEST FALLIDO:")
        for f in fails:
            print(f"  - {f}")
        return 1

    print("✓ TEST PASADO: cuatro citas identificadas correctamente")
    return 0


if __name__ == "__main__":
    sys.exit(main())
