# Customización por especialidad

Esta tabla resume qué cambia en el sistema según la especialidad
declarada del despacho. La especialidad se inyecta como variable
`{{ESPECIALIDAD}}` en los prompts que la consumen.

| Especialidad | Sala/jurisdicción TS prioritaria | Patrones de cita reforzados | Tonalidad |
|---|---|---|---|
| **penal** | Sala Segunda TS, AN Sala Penal | Auto de procesamiento, sumario, art. LECrim, ATC | Estricto con literalidad; el contexto penal exige cita exacta del precepto. |
| **civil** | Sala Primera TS | art. CC, art. LEC, contratos, responsabilidad | Énfasis en jurisprudencia clásica + recientes; tonalidad mercantil cuando aparecen sociedades. |
| **mercantil** | Sala Primera (TS) + juzgados de lo mercantil | LSC, Concursal, Marcas, Patentes, Defensa Competencia | Énfasis en normativa especial. Memoria del despacho cobra protagonismo. |
| **administrativo** | Sala Tercera TS, TSJ, TS contencioso | Ley 39/2015, Ley 40/2015, LJCA, contratación pública | Énfasis en jurisprudencia menor (TSJ) y vigencia normativa. |
| **laboral** | Sala Cuarta TS, TSJ, juzgados sociales | ET, LRJS, LGSS, jurisprudencia social menor | Énfasis MASIVO en vigencia histórica (reformas laborales sucesivas). |
| **multidisciplinar** | Todas | Conjunto base | Configuración neutra; el sistema decide según el tipo de cita. |

## Cómo se aplica al sistema

1. El campo `{{ESPECIALIDAD}}` aparece en:
   - `prompts/coordinator-system.md`, sección "Contexto del despacho"
     (que el installer añade durante el volcado).
   - `skill/verificador-jurisprudencia-es/SKILL.md`, frontmatter
     `description`, para que la skill se active mejor con escritos
     de esa especialidad.

2. El installer añade un bloque al final del prompt del coordinador
   con instrucciones específicas (ver la sección "Bloques de
   especialidad" más abajo).

## Bloques de especialidad

### penal

```
CONTEXTO DEL DESPACHO: especialidad penal.
- Prioriza verificación EXACTA de literalidad para citas de la
  Sala Segunda TS. Una sentencia penal mal citada puede causar
  responsabilidad disciplinaria al letrado.
- Para artículos del CP, comprueba SIEMPRE redacción vigente en
  la fecha del hecho (relevancia del art. 9 CP — irretroactividad
  de normas penales desfavorables).
- Memoria del despacho: prioritaria; muchas citas se repiten entre
  asuntos del mismo cliente.
```

### civil

```
CONTEXTO DEL DESPACHO: especialidad civil.
- Sala Primera TS como fuente predominante.
- Para temas sucesorios, atender a derecho foral cuando proceda
  (jurisdicciones autonómicas habilitadas).
```

### mercantil

```
CONTEXTO DEL DESPACHO: especialidad mercantil.
- Énfasis en LSC, Ley Concursal, Defensa Competencia.
- Doctrina relevante: Brocà, Olivencia, Vicent Chuliá, Embid Irujo,
  Sánchez Calero.
```

### administrativo

```
CONTEXTO DEL DESPACHO: especialidad administrativo.
- Sala Tercera TS, TSJ con peso por jurisdicción autonómica.
- Vigencia normativa crítica: Ley 39/2015 y 40/2015 derogaron
  Ley 30/1992; muchos escritos antiguos invocan la redacción
  anterior.
```

### laboral

```
CONTEXTO DEL DESPACHO: especialidad laboral.
- Sala Cuarta TS, TSJ Social.
- VIGENCIA HISTÓRICA CRÍTICA: reformas laborales sucesivas
  (Ley 35/2010, RDL 3/2012, Ley 3/2012, RDL 32/2021, Ley 12/2021)
  cambian sustancialmente el ET. Aplica fecha_referencia con cuidado.
- Memoria del despacho: prioritaria para criterios de la Sala
  Cuarta.
```

### multidisciplinar

```
CONTEXTO DEL DESPACHO: especialidad multidisciplinar.
- Sin priorización específica.
```
