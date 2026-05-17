"""
Tests de comportamiento del coordinador y los sub-agentes con MOCKING.

NO tocan la API de Anthropic ni la red real. Simulan los veredictos
JSON que devolvería cada sub-agente, y verifican que:
  - el renderizador consolida correctamente
  - los estados problemáticos se reportan en el anexo
  - la rama "base caída" produce `dudosa`
  - la rama "cita literal no encontrada en sentencia real" produce `inexacta`

Estos tests cubren las deudas C.4 y A.6 del DEUDAS-CONOCIDAS.md.

Uso:
    pytest pruebas/test_comportamiento.py -v
"""
from __future__ import annotations
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "skill" / "verificador-jurisprudencia-es" / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))
sys.path.insert(0, str(ROOT))

import render_informe as ri  # noqa: E402
from lib.logger import AuditLog  # noqa: E402


# -------- Veredictos canónicos que cada sub-agente puede devolver --------

VEREDICTO_CENDOJ_VERIFICADA = {
    "cita_original": "STS 1234/2024, de 15 de marzo, Sala Primera",
    "tipo": "STS",
    "estado": "verificada",
    "url_canonica": "https://www.poderjudicial.es/search/result/STS-1234-2024",
    "cita_literal_localizada": "el derecho a la indemnización...",
    "observaciones": "Coincide número, sala, fecha y ponente.",
}

VEREDICTO_CENDOJ_INEXACTA = {
    "cita_original": "STS 5678/2024, de 20 de mayo",
    "tipo": "STS",
    "estado": "inexacta",
    "url_canonica": "https://www.poderjudicial.es/search/result/STS-5678-2024",
    "cita_literal_localizada": None,
    "observaciones": ("La sentencia existe pero el texto literal entrecomillado "
                       "no aparece. El holding atribuido no coincide con FJ 3º."),
    "sugerencia_alternativa": "Reescribir la cita sin entrecomillado falso.",
}

VEREDICTO_BOE_VIGENCIA_HISTORICA = {
    "cita_original": "art. 56.1.a) Estatuto Trabajadores",
    "tipo": "ARTICULO",
    "estado": "verificada",
    "url_canonica": "https://www.boe.es/buscar/act.php?id=BOE-A-2015-11430",
    "observaciones": "Artículo existente.",
    "vigencia": {
        "existe_articulo": True,
        "vigente_en_fecha": True,
        "redaccion_vigente": "45 días por año, tope 42 mensualidades",
        "modificaciones": [
            {"fecha": "2012-02-12", "norma": "Ley 3/2012, art. 18"},
        ],
        "alerta_vigencia": ("La redacción de 45 días fue modificada por la "
                             "Ley 3/2012 a 33 días. Para hechos de septiembre "
                             "de 2010 (anterior a la reforma) la redacción "
                             "invocada es la correcta."),
    },
}

VEREDICTO_DOCTRINA_FUTURO = {
    "cita_original": "MARTÍNEZ CALCERRADA 2027",
    "tipo": "DOCTRINA",
    "estado": "no_encontrada",
    "observaciones": "Fecha de publicación futura (2027). Cita fabricada.",
    "sugerencia_alternativa": ("MARTÍNEZ-CALCERRADA Y GÓMEZ, L., 2011, "
                               "Cuestiones actuales en materia de "
                               "responsabilidad civil, ISBN 978-84-8371-483-6."),
}

VEREDICTO_BASE_CAIDA = {
    "cita_original": "STS hipotética bajo CENDOJ caído",
    "tipo": "STS",
    "estado": "dudosa_por_infraestructura",
    "url_canonica": None,
    "observaciones": ("CENDOJ no respondió tras 3 reintentos con espera "
                       "escalada (3s/8s/20s). HTTP 503. Reintentar con "
                       "`verificar.py --resume <session_id>`."),
}

VEREDICTO_DUDOSA_CONTENIDO = {
    "cita_original": "STS 9999/2020 con ponente ambiguo",
    "tipo": "STS",
    "estado": "dudosa_por_contenido",
    "url_canonica": "https://www.poderjudicial.es/search/result/STS-9999-2020",
    "observaciones": ("La sentencia existe con ese número y año, pero el "
                       "ponente listado en CENDOJ no coincide con el citado en "
                       "el escrito (escrito: Pérez; CENDOJ: García). "
                       "Revisión humana recomendada."),
}

VEREDICTO_DUDOSA_LEGACY = {
    # Veredicto en formato antiguo (sin subtipo) — el render debe
    # tratarlo como dudosa_por_contenido por compatibilidad.
    "cita_original": "STS legacy",
    "tipo": "STS",
    "estado": "dudosa",
    "observaciones": "veredicto legacy sin subtipo",
}

VEREDICTO_MEMORIA_CON_ALERTA = {
    # D.2: fuente cae pero hay entrada en memoria del despacho
    "cita_original": "STC 24/1990, de 15 de febrero",
    "tipo": "STC",
    "estado": "verificada_por_memoria_con_alerta",
    "url_canonica": "https://hj.tribunalconstitucional.es/es-ES/Resolucion/Show/1449",
    "observaciones": ("Verificada en memoria del despacho el 2026-05-17. "
                       "La fuente oficial TC no respondía en momento de "
                       "consulta. Conviene revalidar cuando la fuente "
                       "vuelva a estar operativa."),
}

VEREDICTO_FALLBACK_FUENTE_CRUZADA = {
    # D.1: CENDOJ caído, verificada vía BOE
    "cita_original": "STS 4567/2022, de 8 de junio, Pleno",
    "tipo": "STS",
    "estado": "verificada",
    "url_canonica": "https://www.boe.es/buscar/jurisprudencia.php?id=BOE-A-2022-XXXXX",
    "observaciones": ("Verificada vía BOE (boe.es/buscar/jurisprudencia) "
                       "porque CENDOJ no respondía en momento de consulta. "
                       "Sentencia coincide con datos del escrito."),
}


# ----------------------- Tests sobre render -----------------------

def test_render_consolida_5_estados_distintos():
    veredictos = [
        VEREDICTO_CENDOJ_VERIFICADA,
        VEREDICTO_CENDOJ_INEXACTA,
        VEREDICTO_BOE_VIGENCIA_HISTORICA,
        VEREDICTO_DOCTRINA_FUTURO,
        VEREDICTO_BASE_CAIDA,            # dudosa_por_infraestructura
        VEREDICTO_DUDOSA_CONTENIDO,      # dudosa_por_contenido
    ]
    md = ri.render(veredictos, {"documento_origen": "test.md"})
    # Resumen ejecutivo
    assert "Verificadas: **2**" in md
    assert "Inexactas: **1**" in md
    assert "No encontradas: **1**" in md
    assert "Dudosas por infraestructura: **1**" in md
    assert "Dudosas por contenido: **1**" in md
    # Anexos separados
    assert "Anexo de riesgo: requieren revisión humana por contenido" in md
    assert "Anexo de infraestructura: pendientes de revalidación" in md
    # Inexacta y dudosa_por_contenido en el anexo de riesgo
    assert "STS 5678/2024" in md
    assert "STS 9999/2020" in md
    # Dudosa_por_infraestructura en el anexo de infraestructura
    assert "STS hipotética bajo CENDOJ caído" in md
    # CTA explícito para reintento
    assert "--resume" in md
    # Anexo de vigencia normativa
    assert "Anexo de vigencia normativa" in md
    assert "Ley 3/2012" in md


def test_render_dudosa_infraestructura_no_falsa_verificada():
    veredictos = [VEREDICTO_BASE_CAIDA]
    md = ri.render(veredictos, {"documento_origen": "test.md"})
    bloque_resumen = md.split("Tabla por cita")[0]
    assert "Verificadas: **0**" in bloque_resumen
    assert "Dudosas por infraestructura: **1**" in bloque_resumen
    assert "Dudosas por contenido: **0**" in bloque_resumen
    # CTA para reintento debe aparecer
    assert "verificar.py --resume" in md
    # Mensaje claro de fuente caída
    assert "503" in md or "no respondió" in md.lower()


def test_render_dudosa_contenido_se_lista_en_anexo_de_riesgo():
    veredictos = [VEREDICTO_DUDOSA_CONTENIDO]
    md = ri.render(veredictos, {"documento_origen": "test.md"})
    assert "Anexo de riesgo: requieren revisión humana por contenido" in md
    assert "Anexo de infraestructura" not in md
    assert "ponente" in md.lower()


def test_render_dudosa_legacy_se_trata_como_contenido():
    """Compatibilidad: si un sub-agente devuelve `dudosa` plano (sin
    subtipo), el render lo normaliza a dudosa_por_contenido."""
    veredictos = [VEREDICTO_DUDOSA_LEGACY]
    md = ri.render(veredictos, {"documento_origen": "test.md"})
    assert "Dudosas por contenido: **1**" in md
    assert "Dudosas por infraestructura: **0**" in md


def test_render_verificada_por_memoria_con_alerta(tmp_path: Path):
    """D.2: estado de memoria con alerta cuenta como verificada y
    el por_memoria refleja esta entrada."""
    veredictos = [VEREDICTO_MEMORIA_CON_ALERTA]
    md = ri.render(veredictos, {"documento_origen": "test.md"})
    assert "Verificadas: **1**" in md
    assert "de ellas 1 por memoria" in md
    assert "verificada_por_memoria_con_alerta" in md
    # NO debe aparecer en anexo de riesgo ni de infraestructura
    assert "Anexo de riesgo" not in md
    assert "Anexo de infraestructura" not in md


def test_render_fallback_fuente_cruzada(tmp_path: Path):
    """D.1: una verificada por BOE (fuente alternativa) sigue contando
    como verificada y el motivo se documenta en observaciones."""
    veredictos = [VEREDICTO_FALLBACK_FUENTE_CRUZADA]
    md = ri.render(veredictos, {"documento_origen": "test.md"})
    assert "Verificadas: **1**" in md
    # La URL canónica debe ser la del BOE (fuente que sí respondió)
    assert "boe.es/buscar/jurisprudencia" in md
    # El motivo del fallback aparece en la tabla
    assert "Verificada vía BOE" in md or "CENDOJ no respondía" in md


def test_render_combinacion_d1_d2_d3():
    """Escenario realista mixto: una verificada vía fuente cruzada,
    una memoria con alerta, una dudosa por infraestructura (sin
    memoria previa), una verificación normal y una inexacta."""
    veredictos = [
        VEREDICTO_CENDOJ_VERIFICADA,
        VEREDICTO_FALLBACK_FUENTE_CRUZADA,     # D.1
        VEREDICTO_MEMORIA_CON_ALERTA,           # D.2
        VEREDICTO_BASE_CAIDA,                   # sin memoria → infraestructura
        VEREDICTO_CENDOJ_INEXACTA,
    ]
    md = ri.render(veredictos, {"documento_origen": "test.md"})
    # 3 verificadas (incluyendo memoria con alerta), 1 inexacta, 1 dudosa_infra
    assert "Verificadas: **3**" in md
    assert "de ellas 1 por memoria" in md
    assert "Inexactas: **1**" in md
    assert "Dudosas por infraestructura: **1**" in md
    assert "Dudosas por contenido: **0**" in md
    # Anexos correctos
    assert "Anexo de riesgo: requieren revisión humana por contenido" in md
    assert "Anexo de infraestructura: pendientes de revalidación" in md
    assert "--resume" in md


def test_render_cita_literal_inexacta_no_se_falsa_verifica():
    veredictos = [VEREDICTO_CENDOJ_INEXACTA]
    md = ri.render(veredictos, {"documento_origen": "test.md"})
    bloque_resumen = md.split("Tabla por cita")[0]
    assert "Verificadas: **0**" in bloque_resumen
    assert "Inexactas: **1**" in bloque_resumen
    assert "no aparece" in md.lower() or "no coincide" in md.lower()


def test_render_vigencia_historica_marca_alerta():
    veredictos = [VEREDICTO_BOE_VIGENCIA_HISTORICA]
    md = ri.render(veredictos, {"documento_origen": "test.md"})
    assert "Anexo de vigencia normativa" in md
    assert "Ley 3/2012" in md


def test_render_sin_problemas_no_anexa_riesgo():
    veredictos = [VEREDICTO_CENDOJ_VERIFICADA]
    md = ri.render(veredictos, {"documento_origen": "test.md"})
    assert "Anexo de riesgo" not in md


# ----------------------- Tests sobre logger -----------------------

def test_audit_log_escribe_jsonl(tmp_path: Path):
    log = AuditLog("sesn_test_abc", logs_dir=tmp_path)
    log.event("session_created", documento="prueba.md")
    log.event("subagent_spawn", agent_name="verificador-cendoj")
    log.event("veredicto_consolidado", cita="STS X", estado="verificada")
    lines = log.path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 3
    import json
    parsed = [json.loads(line) for line in lines]
    assert parsed[0]["kind"] == "session_created"
    assert parsed[1]["agent_name"] == "verificador-cendoj"
    assert parsed[2]["estado"] == "verificada"
    # Cada línea tiene timestamp ISO + session id
    for r in parsed:
        assert "ts" in r and "T" in r["ts"]
        assert r["session"] == "sesn_test_abc"


def test_audit_log_concurrente(tmp_path: Path):
    """El logger debe ser thread-safe."""
    import threading
    log = AuditLog("sesn_concurr", logs_dir=tmp_path)

    def worker(i: int):
        for j in range(50):
            log.event("worker_event", worker=i, n=j)

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    lines = log.path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 200  # 4 workers × 50 eventos
    import json
    for line in lines:
        # Cada línea debe ser JSON parseable (no corrompida por race)
        json.loads(line)


# ----------------------- Tests sobre retry -----------------------

def test_retry_no_reintenta_bad_request():
    """Un 400 BadRequest NO debe reintentarse."""
    from lib.retry import retry_api
    import anthropic
    import httpx

    intentos = {"n": 0}

    class FakeBadRequest(anthropic.BadRequestError):
        def __init__(self):
            self.status_code = 400
            self.message = "fake"
            self.body = {"error": {"type": "invalid_request_error"}}

    @retry_api(max_attempts=4)
    def llamada():
        intentos["n"] += 1
        raise FakeBadRequest()

    with pytest.raises(anthropic.BadRequestError):
        llamada()
    assert intentos["n"] == 1  # SOLO un intento, NO reintentos


def test_retry_reintenta_overloaded():
    """Un 529 overloaded SÍ debe reintentarse."""
    from lib.retry import retry_api
    import anthropic

    intentos = {"n": 0}

    class FakeOverloaded(anthropic.InternalServerError):
        def __init__(self):
            self.status_code = 529
            self.message = "fake"
            self.body = {"error": {"type": "overloaded_error"}}

    @retry_api(max_attempts=3, base_delay=0.01, max_delay=0.05)
    def llamada():
        intentos["n"] += 1
        if intentos["n"] < 3:
            raise FakeOverloaded()
        return "ok"

    assert llamada() == "ok"
    assert intentos["n"] == 3  # reintenta hasta éxito
