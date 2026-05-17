"""
Customizador en runtime del Verificador Legal de Bilbao.AI.

Este script se ejecuta DURANTE la instalación (paso 3 y paso 6 del
SKILL.md del installer). El skill instalador lo invoca con los
parámetros del despacho recogidos en la conversación.

Uso:
    python3 scripts/customizar.py \\
        --system-source assets/system-template \\
        --system-dest ~/Documents/verificador-juris-bilbao \\
        --plugin-source assets/plugin-cliente-template \\
        --plugin-dest /tmp/verificador-legal-perez-asociados \\
        --nombre "Pérez & Asociados" \\
        --slug perez-asociados \\
        --especialidad civil \\
        --jurisdicciones BOPV,DOGC \\
        --project-home ~/Documents/verificador-juris-bilbao \\
        [--update]   # respeta .env, .agent-ids.json, logs/
"""
from __future__ import annotations
import argparse
import datetime
import shutil
import sys
import unicodedata
from pathlib import Path


PLACEHOLDERS_CLAVE = (
    "{{DESPACHO_NOMBRE}}",
    "{{DESPACHO_SLUG}}",
    "{{ESPECIALIDAD}}",
    "{{JURISDICCIONES}}",
    "{{JURISDICCIONES_DESC}}",
    "{{PROJECT_HOME}}",
    "{{INSTALL_TIMESTAMP}}",
)

# Bloques de prompt específicos por especialidad
BLOQUES_ESPECIALIDAD = {
    "penal": """\
CONTEXTO DEL DESPACHO: especialidad penal.
- Prioriza verificación EXACTA de literalidad para citas de la Sala
  Segunda TS. Una sentencia penal mal citada puede causar
  responsabilidad disciplinaria.
- Para artículos del CP: comprueba SIEMPRE redacción vigente en la
  fecha del hecho (art. 9 CP — irretroactividad de normas penales
  desfavorables).
""",
    "civil": """\
CONTEXTO DEL DESPACHO: especialidad civil.
- Sala Primera TS como fuente predominante.
- Atender a derecho foral si las jurisdicciones autonómicas
  habilitadas lo cubren.
""",
    "mercantil": """\
CONTEXTO DEL DESPACHO: especialidad mercantil.
- Énfasis en LSC, Ley Concursal, Defensa Competencia.
- Doctrina relevante: Brocà, Olivencia, Vicent Chuliá, Embid Irujo,
  Sánchez Calero.
""",
    "administrativo": """\
CONTEXTO DEL DESPACHO: especialidad administrativo.
- Sala Tercera TS, TSJ con peso por jurisdicción.
- VIGENCIA NORMATIVA CRÍTICA: Ley 39/2015 y 40/2015 derogaron Ley
  30/1992; muchos escritos antiguos invocan la redacción anterior.
""",
    "laboral": """\
CONTEXTO DEL DESPACHO: especialidad laboral.
- Sala Cuarta TS, TSJ Social.
- VIGENCIA HISTÓRICA CRÍTICA: reformas laborales sucesivas
  (Ley 35/2010, RDL 3/2012, Ley 3/2012, RDL 32/2021, Ley 12/2021)
  cambian el ET sustancialmente. Aplica `fecha_referencia` con
  cuidado.
""",
    "multidisciplinar": """\
CONTEXTO DEL DESPACHO: especialidad multidisciplinar.
- Sin priorización específica.
""",
}

# Detalles de cada boletín autonómico
JURISDICCIONES_INFO = {
    "BOPV": ("euskadi.eus", "País Vasco"),
    "DOGC": ("gencat.cat", "Cataluña"),
    "BOCM": ("bocm.es", "Madrid"),
    "DOGV": ("gva.es", "Comunidad Valenciana"),
    "DOG":  ("xunta.gal", "Galicia"),
    "BOJA": ("juntadeandalucia.es", "Andalucía"),
    "BOA":  ("aragon.es", "Aragón"),
    "BORM": ("borm.es", "Región de Murcia"),
    "DOCM": ("castillalamancha.es", "Castilla-La Mancha"),
    "BON":  ("navarra.es", "Navarra"),
}


def slugificar(nombre: str) -> str:
    """Pérez & Asociados → perez-asociados"""
    s = unicodedata.normalize("NFKD", nombre).encode("ascii", "ignore").decode()
    s = "".join(c if c.isalnum() else "-" for c in s.lower())
    while "--" in s:
        s = s.replace("--", "-")
    return s.strip("-")


def _bloque_jurisdicciones_prompt(juris_csv: str) -> str:
    """Genera el bloque que se inyecta en sub-boe-system.md."""
    if not juris_csv or juris_csv.lower() in ("ninguna", "none", ""):
        return ""
    items = [j.strip().upper() for j in juris_csv.split(",") if j.strip()]
    valid = [j for j in items if j in JURISDICCIONES_INFO]
    if not valid:
        return ""
    lines = ["", "DOMINIOS ADICIONALES PERMITIDOS PARA NORMATIVA AUTONÓMICA:"]
    for code in valid:
        domain, region = JURISDICCIONES_INFO[code]
        lines.append(f"- {domain} ({code} — {region})")
    lines.append("")
    lines.append("Aplica los mismos criterios de verificación de vigencia "
                 "normativa que para el BOE estatal.")
    return "\n".join(lines)


def _bloque_jurisdicciones_desc(juris_csv: str) -> str:
    """Genera el sufijo para la description del skill local."""
    if not juris_csv or juris_csv.lower() in ("ninguna", "none", ""):
        return ""
    items = [j.strip().upper() for j in juris_csv.split(",") if j.strip()]
    valid = [j for j in items if j in JURISDICCIONES_INFO]
    if not valid:
        return ""
    return f", normativa autonómica de {', '.join(valid)}"


def _sustituye(text: str, mapping: dict[str, str]) -> str:
    for k, v in mapping.items():
        text = text.replace(k, v)
    return text


def _copiar_con_sustitucion(src: Path, dst: Path, mapping: dict[str, str],
                              respeta: set[str]) -> None:
    """Copia src → dst recursivamente aplicando sustituciones.
    Si dst/<archivo> está en `respeta`, NO se sobreescribe."""
    for src_path in src.rglob("*"):
        if "__pycache__" in src_path.parts or src_path.suffix == ".pyc":
            continue
        rel = src_path.relative_to(src)
        dst_path = dst / rel
        if src_path.is_dir():
            dst_path.mkdir(parents=True, exist_ok=True)
            continue
        # Modo update: respetar ficheros listados
        if str(rel) in respeta and dst_path.exists():
            print(f"  [keep]  {rel}")
            continue
        dst_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            text = src_path.read_text(encoding="utf-8")
            text = _sustituye(text, mapping)
            dst_path.write_text(text, encoding="utf-8")
        except UnicodeDecodeError:
            # binario
            shutil.copy2(src_path, dst_path)
        # Preservar permisos ejecutables
        if src_path.stat().st_mode & 0o111:
            dst_path.chmod(0o755)


def _inyectar_bloque_especialidad(system_dest: Path, especialidad: str) -> None:
    """Añade el bloque de especialidad al final del coordinator-system.md."""
    coord = system_dest / "prompts" / "coordinator-system.md"
    if not coord.exists():
        return
    bloque = BLOQUES_ESPECIALIDAD.get(especialidad.lower(),
                                       BLOQUES_ESPECIALIDAD["multidisciplinar"])
    contenido = coord.read_text(encoding="utf-8")
    marcador = "\n\n## CONTEXTO_DESPACHO_INJECTED\n"
    if marcador in contenido:
        # Modo update: reemplazar bloque previo
        antes = contenido.split(marcador)[0]
        contenido = antes + marcador + bloque
    else:
        contenido += marcador + bloque
    coord.write_text(contenido, encoding="utf-8")


def _inyectar_bloque_jurisdicciones(system_dest: Path, juris_csv: str) -> None:
    """Añade el bloque de jurisdicciones al final del sub-boe-system.md."""
    sub_boe = system_dest / "prompts" / "sub-boe-system.md"
    if not sub_boe.exists():
        return
    bloque = _bloque_jurisdicciones_prompt(juris_csv)
    contenido = sub_boe.read_text(encoding="utf-8")
    marcador = "\n\n## JURISDICCIONES_AUTONOMICAS_INJECTED\n"
    if marcador in contenido:
        antes = contenido.split(marcador)[0]
        contenido = antes + (marcador + bloque if bloque else "")
    elif bloque:
        contenido += marcador + bloque
    sub_boe.write_text(contenido, encoding="utf-8")


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--system-source", required=True, type=Path)
    p.add_argument("--system-dest", required=True, type=Path)
    p.add_argument("--plugin-source", required=True, type=Path)
    p.add_argument("--plugin-dest", required=True, type=Path)
    p.add_argument("--nombre", required=True)
    p.add_argument("--slug", default=None)
    p.add_argument("--especialidad", required=True,
                    choices=("penal", "civil", "mercantil", "administrativo",
                              "laboral", "multidisciplinar"))
    p.add_argument("--jurisdicciones", default="")
    p.add_argument("--project-home", required=True, type=Path)
    p.add_argument("--update", action="store_true",
                    help="Modo update: respetar .env, .agent-ids.json, logs/")
    args = p.parse_args()

    slug = args.slug or slugificar(args.nombre)
    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()

    mapping = {
        "{{DESPACHO_NOMBRE}}": args.nombre,
        "{{DESPACHO_SLUG}}": slug,
        "{{ESPECIALIDAD}}": args.especialidad,
        "{{JURISDICCIONES}}": args.jurisdicciones or "ninguna",
        "{{JURISDICCIONES_DESC}}": _bloque_jurisdicciones_desc(args.jurisdicciones),
        "{{PROJECT_HOME}}": str(args.project_home.expanduser().resolve()),
        "{{INSTALL_TIMESTAMP}}": timestamp,
    }

    # 1) Volcar system-template → system-dest
    print(f"Volcando system-template → {args.system_dest} ...")
    respeta_update: set[str] = set()
    if args.update:
        respeta_update = {".env", ".agent-ids.json"}
    args.system_dest.mkdir(parents=True, exist_ok=True)
    _copiar_con_sustitucion(args.system_source, args.system_dest,
                              mapping, respeta_update)

    # 2) Inyectar bloques específicos
    _inyectar_bloque_especialidad(args.system_dest, args.especialidad)
    _inyectar_bloque_jurisdicciones(args.system_dest, args.jurisdicciones)

    # 3) Volcar plugin-template → plugin-dest
    print(f"Volcando plugin-template → {args.plugin_dest} ...")
    if args.plugin_dest.exists() and not args.update:
        shutil.rmtree(args.plugin_dest)
    args.plugin_dest.mkdir(parents=True, exist_ok=True)
    _copiar_con_sustitucion(args.plugin_source, args.plugin_dest,
                              mapping, set())

    print()
    print(f"✓ System listo en: {args.system_dest}")
    print(f"✓ Plugin listo en: {args.plugin_dest}")
    print(f"  Slug aplicado: {slug}")
    print(f"  Especialidad: {args.especialidad}")
    print(f"  Jurisdicciones: {args.jurisdicciones or 'ninguna'}")
    print()
    print("Próximos pasos:")
    print(f"  1. cd {args.system_dest}")
    print(f"  2. (asegurar que .env tiene ANTHROPIC_API_KEY)")
    print(f"  3. bash bootstrap.sh")
    print(f"  4. cp -r {args.plugin_dest} ~/.config/claude-cowork/plugins/")
    print(f"  5. reiniciar Cowork")
    return 0


if __name__ == "__main__":
    sys.exit(main())
