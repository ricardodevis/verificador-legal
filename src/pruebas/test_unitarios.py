"""
Tests unitarios sobre los scripts deterministas del skill.

Estos tests NO tocan la API de Anthropic ni la red. Se ejecutan en
local con pytest y son los que validan que el motor de extracción y
el renderizador funcionan correctamente.

Uso:
    pytest pruebas/test_unitarios.py -v
"""
from __future__ import annotations
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "skill" / "verificador-jurisprudencia-es" / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import extraer_citas  # noqa: E402
import normalizar_referencias as nr  # noqa: E402
import render_informe as ri  # noqa: E402


# ------------------------------- extraer_citas ----------------------------

def test_extrae_sts_con_numero_y_fecha():
    texto = ("El presente recurso se funda, entre otros argumentos, en la "
             "STS 1234/2024, de 15 de marzo, Sala Primera.")
    citas = extraer_citas.extraer(texto)
    assert any(c["tipo"] == "STS" for c in citas)
    sts = [c for c in citas if c["tipo"] == "STS"][0]
    assert sts["datos"].get("numero") == "1234/2024"


def test_extrae_stc_y_ley():
    texto = ("Conforme a la STC 124/2023 y al artículo 14 de la "
             "Ley 40/2015, procede...")
    citas = extraer_citas.extraer(texto)
    tipos = {c["tipo"] for c in citas}
    assert "STC" in tipos
    assert "LEY" in tipos


def test_extrae_stjue_schrems():
    texto = ("La STJUE de 16 de julio de 2020, asunto C-311/18 "
             "(Schrems II), declaró inválida la Decisión 2016/1250.")
    citas = extraer_citas.extraer(texto)
    assert any(c["tipo"] == "STJUE" for c in citas)
    stjue = [c for c in citas if c["tipo"] == "STJUE"][0]
    assert stjue["datos"].get("asunto") == "C-311/18"


def test_extrae_reglamento_y_directiva():
    texto = ("Bajo el Reglamento (UE) 2016/679 y la Directiva 2019/770/UE...")
    citas = extraer_citas.extraer(texto)
    tipos = {c["tipo"] for c in citas}
    assert "REGLAMENTO_UE" in tipos
    assert "DIRECTIVA" in tipos


def test_no_descarta_silenciosamente_un_match_dificil():
    # Una STS sin número ni fecha — debe detectarse por el verbo "STS"
    texto = "La STS antes citada, dictada por la Sala Primera, sostiene..."
    citas = extraer_citas.extraer(texto)
    # Al menos un STS detectado, aunque sea con datos vacíos
    assert any(c["tipo"] == "STS" for c in citas)


# ------------------------------- normalizar -------------------------------

def test_fecha_imposible_31_febrero():
    # El 31 de febrero NO existe — la normalización debe devolver None
    assert nr.parsear_fecha_es("31 de febrero de 2024") is None


def test_fecha_valida():
    assert nr.parsear_fecha_es("15 de marzo de 2024") == "2024-03-15"


def test_enrutamiento_sub_agentes():
    casos = [
        ({"tipo": "STS"}, "cendoj"),
        ({"tipo": "STC"}, "tc"),
        ({"tipo": "STJUE"}, "eurlex"),
        ({"tipo": "REGLAMENTO_UE"}, "eurlex"),
        ({"tipo": "LEY"}, "boe"),
        ({"tipo": "ARTICULO"}, "boe"),
        ({"tipo": "DOCTRINA"}, "doctrina"),
        ({"tipo": "DESCONOCIDO"}, "no_estructurada"),
    ]
    for cita, esperado in casos:
        assert nr.enrutar(cita) == esperado, f"falla con {cita}"


def test_normalizar_cendoj_marca_fecha_imposible():
    cita = {
        "tipo": "STS",
        "texto_original": "STS 8745/2024, de 31 de febrero",
        "datos": {"numero": "8745/2024", "fecha": "31 de febrero de 2024"},
    }
    out = nr.normalizar_para_cendoj(cita)
    assert out.get("fecha") is None
    assert "fecha_imposible" in out


# ------------------------------- render -----------------------------------

def test_render_minimo():
    veredictos = [{
        "cita_original": "STC 124/2023",
        "tipo": "STC",
        "estado": "verificada",
        "url_canonica": "https://hj.tribunalconstitucional.es/...",
        "observaciones": "Existe y coincide",
    }]
    md = ri.render(veredictos, {"documento_origen": "test.md"})
    assert "# Informe de auditoría" in md
    assert "STC 124/2023" in md
    assert "hj.tribunalconstitucional.es" in md
    assert "100.0%" in md or "100%" in md


def test_render_con_problemas_incluye_anexo():
    veredictos = [
        {"cita_original": "STC 124/2023", "tipo": "STC",
         "estado": "verificada", "url_canonica": "https://hj.tribunalconstitucional.es/x"},
        {"cita_original": "STS 8745/2024", "tipo": "STS",
         "estado": "no_encontrada",
         "observaciones": "Fecha imposible (31 feb)",
         "sugerencia_alternativa": "Revisar fecha"},
    ]
    md = ri.render(veredictos, {"documento_origen": "test.md"})
    assert "Anexo de riesgo" in md
    assert "Fecha imposible" in md


def test_render_bloque_oculto_para_grader():
    md = ri.render([], {"documento_origen": "test.md"})
    assert "<!--" in md
    assert "COBERTURA" in md
