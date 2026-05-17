# Flujo de instalación — diagrama completo

```
┌─────────────────────────────────────────────────────────────────┐
│ Usuario: /instalar-verificador-legal                              │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ Paso 0 — Detectar modo                                          │
│   ¿Existe <dir>/.agent-ids.json?                                │
│   NO → INSTALACIÓN NUEVA                                         │
│   SÍ → preguntar UPDATE vs REINSTALAR                            │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ Paso 1 — Recoger datos (conversación)                           │
│   1.1 Nombre del despacho → slug                                 │
│   1.2 Especialidad (penal/civil/mercantil/admin/laboral/multi)   │
│   1.3 Jurisdicciones autonómicas (lista CSV o "ninguna")        │
│   1.4 Directorio (default ~/Documents/verificador-juris-bilbao) │
│   1.5 API key de Anthropic (sin imprimir)                       │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ Paso 2 — Validaciones previas                                   │
│   python3 ≥ 3.10, pip3, conectividad a api.anthropic.com,        │
│   auth contra la API. Si algo falla → ABORT.                     │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ Paso 3 — Volcar system-template/ con customizaciones            │
│   Copia assets/system-template/ → <dir>/                         │
│   Sustituir {{DESPACHO_NOMBRE}}, {{ESPECIALIDAD}},               │
│   {{JURISDICCIONES}} en los ficheros listados.                   │
│   En modo UPDATE: NO sobrescribir .env, .agent-ids.json, logs/   │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ Paso 4 — Crear <dir>/.env (chmod 600)                           │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ Paso 5 — Ejecutar bootstrap.sh                                  │
│   bash <dir>/bootstrap.sh                                        │
│   Captura stdout/stderr. Si falla → consultar troubleshooting.md │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ Paso 6 — Construir plugin cliente                               │
│   Copia plugin-cliente-template/ a temporal.                     │
│   Sustituye {{DESPACHO_NOMBRE}}, {{DESPACHO_SLUG}},              │
│   {{PROJECT_HOME}}.                                              │
│   Renombra a verificador-legal-<slug>.                           │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ Paso 7 — Instalar plugin en ~/.config/claude-cowork/plugins/    │
│   Recomendar reinicio de Cowork (sin hacerlo automáticamente)    │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ Paso 8 — (opcional, con confirmación) Test E2E                  │
│   verificar.py pruebas/escrito-de-prueba.md ...                 │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ Paso 9 — Reporte final al usuario                               │
└─────────────────────────────────────────────────────────────────┘
```

## Decisiones en cada paso

- Si el usuario quiere cancelar en cualquier paso: respetar.
  Limpiar artefactos parciales si conviene (preguntando).
- Si el usuario quiere reanudar tras un fallo: aceptar el modo
  UPDATE y continuar desde donde estaba.

## Idempotencia

El installer es idempotente. Cada paso es seguro de re-ejecutar:

- Paso 3 (volcado): sobreescribe ficheros que no sean del despacho.
- Paso 4 (.env): pide confirmación si ya existe.
- Paso 5 (bootstrap): los scripts de despliegue son idempotentes
  (respetan IDs previos en .agent-ids.json).
- Paso 6-7 (plugin): sobreescribe sin pérdida (los IDs viven en el
  proyecto, no en el plugin).
- Paso 8 (test): consume tokens cada vez; pide confirmación expresa.
