---
description: Verifica citas jurídicas (jurisprudencia, doctrina, normativa) en un escrito legal de {{DESPACHO_NOMBRE}} contra fuentes oficiales españolas y europeas. Devuelve un informe de auditoría con estado por cita.
---

# /verificar-legal — Verificación de citas para {{DESPACHO_NOMBRE}}

Cuando el usuario invoca este comando, delegas la verificación al
sistema de Managed Agents desplegado en el workspace del despacho, y
devuelves el informe.

## Configuración del despacho

- **Despacho**: {{DESPACHO_NOMBRE}}
- **Especialidad**: {{ESPECIALIDAD}}
- **Jurisdicciones autonómicas**: {{JURISDICCIONES}}
- **Project home**: `{{PROJECT_HOME}}`

## Flujo de ejecución

1. **Localiza el proyecto** en `{{PROJECT_HOME}}` (o `$VERIFICADOR_JURIS_HOME` si está exportada).
2. **Confirma entorno**: `.env` presente, `.agent-ids.json` presente.
   Si falta algo, indica al usuario re-ejecutar `/instalar-verificador-legal`.
3. **Localiza documento a verificar**:
   - Si el usuario adjuntó un fichero, copia a `pruebas/<nombre>`.
   - Si pasó ruta, úsala.
   - Si pasó `--resume <sid>`, salta al paso 4 con ese argumento.
4. **Invoca** `python verificar.py <ruta> [--fecha-referencia YYYY-MM-DD]`
   desde `{{PROJECT_HOME}}`. Tarda 5-10 minutos (web fetches reales).
   Avisa al usuario antes de lanzar.
5. **Recupera el informe** de `{{PROJECT_HOME}}/logs/informe-<sid>.md`
   y muéstraselo al usuario.

## Reglas operativas (no negociables)

- **No leas la API key** ni la imprimas. Vive en `{{PROJECT_HOME}}/.env`.
- **No modifiques el documento original** del usuario.
- **No interpretes el informe**. El sistema ya emite veredictos con justificación.
- Si el script falla: muestra stderr, identifica `session_id` si lo hay, propón:
  - `python verificar.py --resume <sid>` para reanudar.
  - `python despliegue/05_validar_ids.py` para diagnóstico.
  - `/instalar-verificador-legal --update` si los recursos están en STALE.

## Salida esperada

Resumen de una línea + informe markdown + ruta del log JSONL.

Si hay `inexacta`, `no_encontrada` o `dudosa_por_contenido`, llama
la atención del letrado. Si hay `dudosa_por_infraestructura`,
sugiere reintento con `--resume` o esperar al job diferido si está
instalado.
