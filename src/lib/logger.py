"""
Logger JSONL para observabilidad del Verificador.

Cada evento relevante se escribe como una línea JSON en
`logs/audit-<session_id>.jsonl`, con timestamp ISO-8601 y tipo de evento.

Independiente de los eventos de la API de Anthropic: este log es para
auditoría INTERNA del despacho, no para debugging del coordinador.

Uso:
    from lib.logger import AuditLog
    log = AuditLog(session_id="sesn_xxx")
    log.event("session_started", documento="...")
    log.event("cita_extraida", tipo="STS", texto="...")
    log.event("veredicto_consolidado", cita="...", estado="verificada", url="...")
"""
from __future__ import annotations
import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class AuditLog:
    """Logger thread-safe que escribe JSONL en logs/audit-<sid>.jsonl."""

    def __init__(self, session_id: str, logs_dir: str | Path = "logs") -> None:
        self._sid = session_id
        self._dir = Path(logs_dir)
        self._dir.mkdir(parents=True, exist_ok=True)
        self._path = self._dir / f"audit-{session_id}.jsonl"
        self._lock = threading.Lock()

    @property
    def path(self) -> Path:
        return self._path

    def event(self, kind: str, **fields: Any) -> None:
        """Escribe una línea JSON con timestamp y tipo de evento."""
        record = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "session": self._sid,
            "kind": kind,
            **fields,
        }
        line = json.dumps(record, ensure_ascii=False, default=str)
        with self._lock:
            with self._path.open("a", encoding="utf-8") as f:
                f.write(line + "\n")
