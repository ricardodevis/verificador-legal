"""
Entry point para verificar las citas jurídicas de un escrito.

Uso:
    python verificar.py <fichero>
    python verificar.py --resume <session_id>
    python verificar.py --fecha-referencia 2018-03-15 <fichero>
    python verificar.py --json-only <fichero>   # solo imprime path informe

Flujo (modo normal):
  1. Sube el documento a la Files API.
  2. Sube la rúbrica como fichero.
  3. Crea un environment cloud con red sin restringir.
  4. Crea una sesión que referencia al coordinador, monta el documento
     y adjunta el Memory Store con `read_write`.
  5. Envía `user.define_outcome` con la rúbrica.
  6. Stremea eventos hasta que la sesión cae a idle o se cumple un
     wall-clock deadline.
  7. Descarga `informe.md` a `logs/`.

Flujo --resume:
  Continúa streaming desde una sesión existente. No recrea recursos
  ni vuelve a subir documento. Útil si el cliente se cae a mitad de
  ejecución y la sesión en cloud sigue viva.

NO se escribe la API key ni en logs ni en outputs.
"""
from __future__ import annotations
import argparse
import json
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
import anthropic

load_dotenv()

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from lib.retry import retry_api  # noqa: E402
from lib.logger import AuditLog  # noqa: E402

IDS_FILE = ROOT / ".agent-ids.json"
RUBRICA_FILE = ROOT / "rubrica" / "verificacion-jurisprudencia.md"
LOGS_DIR = ROOT / "logs"
LOGS_DIR.mkdir(exist_ok=True)

BETAS_MA = ["managed-agents-2026-04-01"]
BETAS_FILES = ["files-api-2025-04-14"]
BETAS_BOTH = BETAS_MA + BETAS_FILES

MAX_WALLCLOCK_SECONDS = int(os.environ.get("VERIFICAR_MAX_SECONDS", "1800"))
MAX_ITER = int(os.environ.get("COORDINATOR_MAX_ITERATIONS", "3"))


def cargar_ids() -> dict:
    if not IDS_FILE.exists():
        print("Error: .agent-ids.json no existe. Ejecuta los scripts "
              "de despliegue primero.", file=sys.stderr)
        sys.exit(1)
    return json.loads(IDS_FILE.read_text(encoding="utf-8"))


# Wrappers con retry para las llamadas API
@retry_api(max_attempts=4)
def _upload_file(client, file_tuple, *, betas):
    return client.beta.files.upload(file=file_tuple, betas=betas)


@retry_api(max_attempts=4)
def _create_environment(client, **kwargs):
    return client.beta.environments.create(**kwargs)


@retry_api(max_attempts=4)
def _create_session(client, **kwargs):
    return client.beta.sessions.create(**kwargs)


@retry_api(max_attempts=4)
def _send_events(client, sid, *, events, betas):
    return client.beta.sessions.events.send(sid, events=events, betas=betas)


@retry_api(max_attempts=4)
def _list_files(client, *, scope_id, betas):
    return client.beta.files.list(scope_id=scope_id, betas=betas)


@retry_api(max_attempts=4)
def _download_file(client, fid, *, betas):
    return client.beta.files.download(fid, betas=betas)


def _stream_session(client, log: AuditLog, session_id: str, deadline: float):
    """Stream eventos de una sesión y devuelve (final_result, iteraciones).

    final_result puede ser: 'satisfied', 'needs_revision', 'failed',
    'max_iterations_reached', 'interrupted', None (timeout o stream caído).
    """
    final_result = None
    iteraciones = 0
    print(f"  → streaming eventos (deadline {MAX_WALLCLOCK_SECONDS}s)...")
    log.event("stream_open", session_id=session_id)
    with client.beta.sessions.events.stream(session_id, betas=BETAS_MA) as stream:
        for event in stream:
            if time.monotonic() > deadline:
                print("    ! wall-clock deadline alcanzado")
                log.event("stream_deadline_reached")
                break
            t = getattr(event, "type", "?")
            if t == "session.thread_created":
                name = getattr(event, "agent_name", "?")
                print(f"    [spawn] {name}")
                log.event("subagent_spawn", agent_name=name)
            elif t == "agent.thread_message_received":
                src = getattr(event, "from_agent_name", "?")
                print(f"    [report] {src} returned")
                log.event("subagent_report", from_agent=src)
            elif t == "span.outcome_evaluation_start":
                it = getattr(event, "iteration", "?")
                iteraciones += 1
                print(f"    [grader] iteración {it} start")
                log.event("grader_iteration_start", iteration=it)
            elif t == "span.outcome_evaluation_end":
                final_result = getattr(event, "result", None)
                expl = getattr(event, "explanation", "")[:240]
                print(f"    [grader] result={final_result} — {expl}")
                log.event("grader_iteration_end",
                          result=final_result,
                          explanation=getattr(event, "explanation", "")[:1000])
                if final_result in ("satisfied", "failed", "max_iterations_reached"):
                    break
            elif t == "session.status_idle":
                log.event("session_idle")
                if final_result is not None:
                    break
            elif t == "session.status_terminated":
                print("    [session] terminated")
                log.event("session_terminated")
                break
    return final_result, iteraciones


def _recuperar_informe(client, log: AuditLog, session_id: str) -> str | None:
    """Recupera /mnt/session/outputs/informe.md con indexing-lag retry."""
    for intento in range(4):
        time.sleep(2 + intento * 2)
        try:
            files = _list_files(client, scope_id=session_id, betas=BETAS_BOTH)
        except Exception as exc:
            print(f"    ! list files falló (intento {intento+1}): {exc}")
            continue
        for f in files.data:
            if f.filename.endswith("informe.md"):
                content = _download_file(client, f.id, betas=BETAS_FILES)
                data = content.read() if hasattr(content, "read") else bytes(content)
                text = data.decode("utf-8")
                log.event("informe_downloaded", file_id=f.id, length=len(text))
                return text
    log.event("informe_not_found_after_retries")
    return None


def comando_normal(args, client, ids) -> int:
    documento = Path(args.fichero).resolve()
    if not documento.exists():
        print(f"Error: {documento} no existe", file=sys.stderr)
        return 1

    coord = ids["coordinador"]
    memory_store_id = ids["memory_store"]["id"]
    print(f"Verificando: {documento.name}")
    print(f"Coordinador: {coord['id']} v{coord['version']}")

    # 1. Documento
    print("  → subiendo documento...")
    with open(documento, "rb") as f:
        doc_file = _upload_file(
            client,
            (documento.name, f.read(), "text/markdown"),
            betas=BETAS_FILES,
        )
    print(f"    {doc_file.id}")

    # 2. Rúbrica
    print("  → subiendo rúbrica...")
    with open(RUBRICA_FILE, "rb") as f:
        rubrica_file = _upload_file(
            client,
            (RUBRICA_FILE.name, f.read(), "text/markdown"),
            betas=BETAS_FILES,
        )
    print(f"    {rubrica_file.id}")

    # 3. Environment
    print("  → creando environment...")
    env = _create_environment(
        client,
        name=f"verif-{int(time.time())}",
        config={"type": "cloud", "networking": {"type": "unrestricted"}},
        betas=BETAS_MA,
    )
    print(f"    {env.id}")

    # 4. Sesión con doc + memory store
    print("  → creando sesión...")
    mount_path = f"/mnt/session/uploads/{documento.name}"
    session = _create_session(
        client,
        agent={"type": "agent", "id": coord["id"], "version": coord["version"]},
        environment_id=env.id,
        title=f"Verificación: {documento.name}",
        resources=[
            {"type": "file", "file_id": doc_file.id, "mount_path": mount_path},
            {
                "type": "memory_store",
                "memory_store_id": memory_store_id,
                "access": "read_write",
                "instructions": (
                    "Memoria de citas verificadas del despacho. Consulta SIEMPRE "
                    "antes de delegar. Disciplina de paths INVIOLABLE (ver coordinator "
                    "system prompt)."
                ),
            },
        ],
        betas=BETAS_MA,
    )
    print(f"    {session.id}")

    log = AuditLog(session.id, logs_dir=LOGS_DIR)
    log.event("session_created",
              documento=documento.name,
              doc_file_id=doc_file.id,
              env_id=env.id,
              coordinador=coord["id"],
              fecha_referencia=args.fecha_referencia)

    # 5. Outcome
    print("  → enviando user.define_outcome...")
    descripcion = (
        f"Verifica todas las citas jurídicas del documento montado en "
        f"{mount_path} conforme a la Skill verificador-jurisprudencia-es. "
        f"Produce el informe de auditoría en /mnt/session/outputs/informe.md."
    )
    if args.fecha_referencia:
        descripcion += (
            f" La fecha de referencia del escrito (para análisis de vigencia "
            f"normativa) es {args.fecha_referencia}."
        )
    _send_events(client, session.id, events=[{
        "type": "user.define_outcome",
        "description": descripcion,
        "rubric": {"type": "file", "file_id": rubrica_file.id},
        "max_iterations": MAX_ITER,
    }], betas=BETAS_MA)
    log.event("outcome_defined", max_iterations=MAX_ITER)

    # 6. Stream
    deadline = time.monotonic() + MAX_WALLCLOCK_SECONDS
    final_result, iteraciones = _stream_session(client, log, session.id, deadline)

    # 7. Recuperar informe
    print("  → recuperando informe...")
    informe = _recuperar_informe(client, log, session.id)
    if informe:
        log_path = LOGS_DIR / f"informe-{session.id}.md"
        log_path.write_text(informe, encoding="utf-8")
        print(f"\n✓ Informe guardado en {log_path}")
        if not args.json_only:
            print("=" * 60)
            print(informe)
            print("=" * 60)
    else:
        print(f"\n! No se encontró informe.md. Sesión: {session.id}")

    log.event("session_finished",
              result=final_result,
              iteraciones=iteraciones)
    print(f"\nResultado: {final_result}  Iter: {iteraciones}  "
          f"Session: {session.id}  Audit: {log.path.name}")
    if args.json_only:
        print(json.dumps({
            "session_id": session.id,
            "result": final_result,
            "iteraciones": iteraciones,
            "informe_path": str(LOGS_DIR / f"informe-{session.id}.md") if informe else None,
            "audit_path": str(log.path),
        }))
    return 0 if final_result == "satisfied" else 2


def comando_resume(args, client, ids) -> int:
    sid = args.resume
    print(f"Reanudando sesión {sid}...")
    log = AuditLog(sid, logs_dir=LOGS_DIR)
    log.event("resume_invoked")
    deadline = time.monotonic() + MAX_WALLCLOCK_SECONDS
    final_result, iteraciones = _stream_session(client, log, sid, deadline)
    print("  → recuperando informe...")
    informe = _recuperar_informe(client, log, sid)
    if informe:
        log_path = LOGS_DIR / f"informe-{sid}.md"
        log_path.write_text(informe, encoding="utf-8")
        print(f"\n✓ Informe guardado en {log_path}")
        if not args.json_only:
            print("=" * 60)
            print(informe)
            print("=" * 60)
    log.event("resume_finished",
              result=final_result, iteraciones=iteraciones)
    print(f"\nResultado: {final_result}  Iter: {iteraciones}  Session: {sid}")
    return 0 if final_result == "satisfied" else 2


def main() -> int:
    p = argparse.ArgumentParser(description="Verificador de jurisprudencia")
    p.add_argument("fichero", nargs="?", help="Documento a verificar")
    p.add_argument("--resume", metavar="SESSION_ID",
                    help="Reanudar streaming de una sesión existente")
    p.add_argument("--fecha-referencia", metavar="YYYY-MM-DD", default=None,
                    help="Fecha del escrito (para análisis de vigencia histórica)")
    p.add_argument("--json-only", action="store_true",
                    help="Output reducido a JSON (no imprime informe en stdout)")
    args = p.parse_args()

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: falta ANTHROPIC_API_KEY", file=sys.stderr)
        return 1
    client = anthropic.Anthropic(api_key=api_key)
    ids = cargar_ids()

    if args.resume:
        return comando_resume(args, client, ids)
    if not args.fichero:
        p.error("se requiere <fichero> o --resume <session_id>")
    return comando_normal(args, client, ids)


if __name__ == "__main__":
    sys.exit(main())
