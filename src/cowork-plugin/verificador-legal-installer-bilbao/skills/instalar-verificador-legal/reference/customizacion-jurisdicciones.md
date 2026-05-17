# Customización por jurisdicciones autonómicas

Cuando el despacho habilita boletines autonómicos, el sub-agente
`verificador-boe` extiende su dominio permitido para incluir esos
boletines como fuentes oficiales adicionales.

## Boletines soportados

| Código | Comunidad | Dominio | URL buscador |
|---|---|---|---|
| BOPV | País Vasco | euskadi.eus | https://www.euskadi.eus/bopv2/datos/Bopv.htm |
| DOGC | Cataluña | gencat.cat | https://dogc.gencat.cat |
| BOCM | Madrid | bocm.es | https://www.bocm.es |
| DOGV | Comunidad Valenciana | gva.es | https://dogv.gva.es |
| DOG | Galicia | xunta.gal | https://www.xunta.gal/diario-oficial-galicia |
| BOJA | Andalucía | juntadeandalucia.es | https://www.juntadeandalucia.es/boja |
| BOA | Aragón | aragon.es | https://www.boa.aragon.es |
| BORM | Región de Murcia | borm.es | https://www.borm.es |
| DOCM | Castilla-La Mancha | castillalamancha.es | https://docm.castillalamancha.es |
| BON | Navarra | navarra.es | https://bon.navarra.es |

## Cómo se aplica al sistema

El campo `{{JURISDICCIONES}}` se inyecta como lista en el system
prompt del sub-agente BOE. Ejemplo si el despacho habilita BOPV y
DOGC:

```
DOMINIOS ADICIONALES PERMITIDOS PARA NORMATIVA AUTONÓMICA:
- euskadi.eus (BOPV — País Vasco)
- gencat.cat (DOGC — Cataluña)

Si una cita normativa hace referencia a:
- Ley o Decreto del Parlamento Vasco / Gobierno Vasco → consultar
  https://www.euskadi.eus/bopv2/
- Llei o Decret del Parlament o Govern de Catalunya → consultar
  https://dogc.gencat.cat

Aplica los mismos criterios de verificación de vigencia normativa
que para el BOE estatal.
```

Si el despacho responde "ninguna", el sub-agente BOE solo trabaja
con normativa estatal y este bloque NO se inyecta.

## Detección automática de normativa autonómica

El sub-agente BOE, al recibir una cita, debe identificar si es
normativa autonómica por patrones:

- "Ley Vasca", "Ley del Parlamento Vasco", "Decreto X/YYYY del
  Gobierno Vasco" → BOPV
- "Llei catalana", "Llei X/YYYY del Parlament" → DOGC
- "Ley X/YYYY de la Comunidad de Madrid" → BOCM
- etc.

Si detecta normativa autonómica de una jurisdicción NO habilitada
por el despacho, debe marcarla `dudosa_por_contenido` con nota:
"Esta cita invoca normativa autonómica de <Comunidad> que no está
habilitada en la configuración del despacho. Para verificarla,
re-ejecutar `/instalar-verificador-legal` y habilitar la
jurisdicción correspondiente."
