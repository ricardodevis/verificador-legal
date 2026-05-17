---
name: verificador-legal-{{DESPACHO_SLUG}}
description: Skill de activación automática del verificador de {{DESPACHO_NOMBRE}}. Activar cuando el usuario aporta escritos jurídicos ({{ESPECIALIDAD}}) con citas a sentencias del Tribunal Supremo, TC, TJUE, TSJ, AP, AN; normas estatales (leyes, RD), normas europeas (Reglamentos UE, Directivas){{JURISDICCIONES_DESC}}; o doctrina académica. Solo se activa cuando se detectan citas jurídicas explícitas — no activar para conversaciones generales sobre derecho. Cuando se active, invocar el comando /verificar-legal con el documento adjunto.
---

# Skill local — Verificador {{DESPACHO_NOMBRE}}

Skill que se carga cuando se detecta material jurídico en lo que el
usuario aporta. Su trabajo: orientar a Cowork para invocar
`/verificar-legal`.

## Configuración del despacho

- **Especialidad principal**: {{ESPECIALIDAD}}
- **Jurisdicciones autonómicas**: {{JURISDICCIONES}}

## Cuándo activarte

- Documentos `.docx`, `.pdf`, `.md`, `.txt` con citas jurídicas.
- Mensajes que mencionen verificación, auditoría, comprobación de
  sentencias.
- Slash command `/verificar-legal` invocado.

## Patrones de cita que disparan activación

- Jurisprudencia: STS, STC, SAN, STSJ, SAP, STJUE, asunto C-X/YY.
- Normativa: Ley X/YYYY, LO X/YYYY, RD X/YYYY, Reglamento (UE) X/YYYY,
  Directiva X/YYYY/UE/CE.
- Doctrina: APELLIDOS, X. + obra + editorial reconocida.
- Doctrina administrativa: DGT V-XXXX-YY, AEPD, CNMV.

## Qué hacer al activarte

1. Si no se ha invocado, invoca `/verificar-legal` con el documento
   adjunto o la ruta indicada.
2. Si solo hay un fragmento de cita en chat: pregunta al usuario si
   tiene escrito completo, sugiere subirlo.
3. **No improvises verificación tú mismo**. Delega al sistema.

## Qué NO hacer

- No marcar como verificada basándote en tu conocimiento general.
- No interpretar la rúbrica del Outcome.
- No leer la API key.
- No alterar el documento original.

## Configuración esperada en el sistema

- Proyecto en `{{PROJECT_HOME}}`.
- `.env` con `ANTHROPIC_API_KEY`.
- `.agent-ids.json` con coordinador, 5 sub-agentes, skill y memory
  store ya desplegados.

Si falta algo: avisar al usuario y proponer `/instalar-verificador-legal`.
