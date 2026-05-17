# Memory Store: jurisprudencia-verificada-despacho

Este directorio describe el esquema del Memory Store. El contenido
real se construye con uso: cada cita verificada por el coordinador
se incorpora aquí automáticamente cuando éste escribe en
`/mnt/memory/jurisprudencia-verificada-despacho/...`.

Esquema documentado en
`skill/verificador-jurisprudencia-es/references/memory-schema.md`.

## Estructura inicial al crear el store

El script `despliegue/04_crear_memory_store.py` siembra el store con:

- `/README.md` (este fichero, accesible al coordinador como contexto)
- `/jurisprudencia/.keep`
- `/normativa/.keep`
- `/doctrina/.keep`

Las subcarpetas (sts/, stc/, etc.) se crean a demanda cuando aparece
la primera entrada de cada categoría.
