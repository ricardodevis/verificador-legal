---
description: Verifica citas jurídicas (jurisprudencia, doctrina, normativa) en un escrito legal contra fuentes oficiales españolas y europeas. Devuelve un informe de auditoría con estado por cita (verificada / verificada_por_memoria / inexacta / no_encontrada / dudosa).
---

# /verificar-legal — Verificación de citas jurídicas

Cuando el usuario invoca este comando, tu trabajo es delegar la
verificación al sistema de Managed Agents desplegado en el workspace
del despacho, y devolverle el informe.

## Argumentos posibles del comando

El usuario puede pasar argumentos opcionales tras `/verificar-legal`:

- Una ruta de fichero (relativa al directorio de trabajo del usuario
  o absoluta): el documento a verificar.
- Un `session_id` precedido de `--resume` para reanudar una sesión
  anterior.
- `--fecha-referencia YYYY-MM-DD` para análisis de vigencia
  normativa en escritos sobre hechos pasados.

Si el usuario NO adjunta documento ni pasa argumentos, pídele que
adjunte un escrito o que indique una ruta. NO inventes uno.

## Flujo de ejecución

1. **Localiza el proyecto del verificador** en la máquina del usuario.
   Por convención vive en `~/Documents/verificador-juris-bilbao/` o
   se ha exportado vía la variable `VERIFICADOR_JURIS_HOME`. Si no lo
   encuentras, dilo y pide que te indique la ruta.

2. **Asegura el entorno**:
   - `cd` al directorio del proyecto.
   - Confirma que existe `.env` con `ANTHROPIC_API_KEY` (NO la imprimas
     en stdout).
   - Confirma que existe `.agent-ids.json` (los agentes están
     desplegados). Si no existe, avisa: "el sistema no está desplegado,
     ejecuta los scripts de `despliegue/` primero".

3. **Localiza el documento a verificar**:
   - Si el usuario adjuntó un fichero en la conversación, cópialo a
     `pruebas/<nombre_original>` dentro del proyecto antes de
     invocar `verificar.py`.
   - Si el usuario pasó una ruta, usa esa.
   - Si el usuario pasó `--resume <sid>`, salta al paso 4 con el
     argumento correspondiente.

4. **Invoca `verificar.py`** con las opciones que correspondan:
   ```
   python verificar.py <ruta> [--fecha-referencia YYYY-MM-DD] [--json-only]
   python verificar.py --resume <session_id>
   ```

   Recuerda que `verificar.py` puede tardar varios minutos (los
   sub-agentes hacen web fetches reales contra CENDOJ/BOE/TC/EUR-Lex).
   Avisa al usuario antes de lanzar: "Esto puede tardar entre 3 y 10
   minutos. Si quieres seguir trabajando en otra cosa, te aviso al
   terminar."

5. **Recupera el informe**:
   - El script imprime el informe a stdout y lo guarda en
     `logs/informe-<session_id>.md`.
   - Coge el contenido del fichero y muéstraselo al usuario en un
     bloque markdown.
   - Indica también la ruta del log de auditoría JSONL en
     `logs/audit-<session_id>.jsonl`, por si quiere inspeccionarlo.

## Reglas operativas (no negociables)

- **No leas la API key** ni la imprimas. Vive en `.env` y solo Python
  la lee en runtime.
- **No modifiques el documento original** del usuario bajo ningún
  concepto. Tu output es el informe en `logs/`.
- **No interpretes el informe** ni decidas tú si las citas son
  válidas — el sistema ya lo hace y emite veredictos con justificación.
- **Si el script falla**, muestra el stderr al usuario, identifica el
  `session_id` si se llegó a crear, y propón:
  - `python verificar.py --resume <sid>` para reanudar.
  - `python despliegue/05_validar_ids.py` si sospechas que algún
    recurso del workspace está STALE o GONE.
- **Si el documento es sensible** (datos personales, secreto
  profesional), recuerda al usuario que se va a subir a la Files API
  de Anthropic. Si el usuario lo prefiere, ofrécele redactarlo antes.

## Salida esperada al usuario

Al terminar, presenta:

1. Un resumen de una línea: cuántas citas detectadas, cuántas
   verificadas, cuántas problemáticas.
2. El informe completo en markdown.
3. La ruta del log JSONL para auditoría profunda.
4. Si hay citas `inexacta` o `no_encontrada`, llama explícitamente la
   atención del usuario en el resumen.

## Ejemplo de invocación

```
Usuario: /verificar-legal [adjunta recurso.docx]
Cowork:  → Detecto recurso.docx adjunto. Lo copio a pruebas/recurso.docx.
         → Lanzando python verificar.py pruebas/recurso.docx
         → Esto va a tardar varios minutos (web fetches reales a CENDOJ/BOE).
         [...]
         → Informe: 12 citas detectadas, 9 verificadas, 2 inexactas, 1 no_encontrada.
         → Atención: la STS 4567/2023 que cita el escrito existe pero la
           cita literal no coincide con el FJ 4º.
         [...informe completo aquí...]
         → Log de auditoría en logs/audit-sesn_xxx.jsonl
```
