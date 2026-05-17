# Job diferido — reintento automático de citas en `dudosa_por_infraestructura`

Cuando una fuente oficial (CENDOJ, BOE, TC, EUR-Lex, Dialnet) no
responde en el momento de la verificación, las citas afectadas quedan
en estado `dudosa_por_infraestructura`. El **job diferido** es un
proceso que se ejecuta periódicamente y reintenta esas citas cuando
la fuente vuelve a estar disponible.

## El script

`despliegue/06_reintentar_pendientes.py` hace:

1. Lee todos los `logs/audit-*.jsonl` de las últimas 72 horas.
2. Identifica sesiones con citas `dudosa_por_infraestructura`.
3. Para cada sesión candidata, ejecuta
   `python3 verificar.py --resume <session_id> --json-only`.
4. Anota el resultado en el propio audit log con el evento
   `pendientes_reintentados`.

Respeta dos cooldowns para no machacar al sistema:

- **`--max-age-hours`** (default 72): no reintenta sesiones más antiguas.
- **`--cooldown-hours`** (default 1): no reintenta la misma sesión si
  ya se reintentó hace menos de N horas.

## Uso manual (verificar si funciona antes de programar)

```bash
cd ~/Documents/verificador-juris-bilbao
python3 despliegue/06_reintentar_pendientes.py --dry-run
# Lista las sesiones candidatas sin lanzarlas. Ideal primer test.

python3 despliegue/06_reintentar_pendientes.py
# Ejecuta los reintentos en serie (sin paralelizar).
```

## Programación periódica — macOS (launchd, recomendado)

Crea el fichero `~/Library/LaunchAgents/ai.bilbao.verificador-pendientes.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
        "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>ai.bilbao.verificador-pendientes</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>-lc</string>
        <string>cd $HOME/Documents/verificador-juris-bilbao &amp;&amp; /usr/bin/env python3 despliegue/06_reintentar_pendientes.py &gt;&gt; logs/cron.log 2&gt;&amp;1</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Minute</key>
        <integer>15</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>/tmp/verificador-pendientes.out</string>
    <key>StandardErrorPath</key>
    <string>/tmp/verificador-pendientes.err</string>
</dict>
</plist>
```

Carga el job:

```bash
launchctl load ~/Library/LaunchAgents/ai.bilbao.verificador-pendientes.plist
launchctl start ai.bilbao.verificador-pendientes
```

Verifica que está activo:

```bash
launchctl list | grep verificador-pendientes
```

Para desinstalar:

```bash
launchctl unload ~/Library/LaunchAgents/ai.bilbao.verificador-pendientes.plist
rm ~/Library/LaunchAgents/ai.bilbao.verificador-pendientes.plist
```

## Programación periódica — Linux (cron)

```bash
crontab -e
```

Añadir línea:

```
15 * * * * cd $HOME/Documents/verificador-juris-bilbao && /usr/bin/env python3 despliegue/06_reintentar_pendientes.py >> logs/cron.log 2>&1
```

## Programación periódica — Cowork scheduled tasks

Si tienes el plugin `cowork-survival-kit:save` o equivalente, puedes
usar la tarea de scheduling de Cowork:

```
/schedule cada hora a y media: python3 despliegue/06_reintentar_pendientes.py
```

(La sintaxis exacta depende de tu versión de Cowork; mira
`scheduled-tasks` en la doc.)

## Coste estimado

Una sesión reanudada con N citas pendientes consume aproximadamente
el mismo coste por cita que la verificación original. Para una
sesión típica con 1-3 citas dudosa_por_infraestructura, suele ser
0,10-0,50 USD por reintento. Si el script se ejecuta cada hora y la
mayoría de horas no hay nada que reintentar (porque las fuentes
oficiales suelen estar arriba), el coste mensual es marginal.

## Privacidad

El job diferido NO envía nada a Bilbao.AI. Todo el trabajo ocurre
entre la máquina del despacho y el workspace de Anthropic del
despacho. Los logs `audit-*.jsonl` viven solo en disco local.

## Apagar el job temporalmente

Si el despacho quiere pausar el reintento autónomo (por ejemplo, por
mantenimiento de su API key):

```bash
launchctl unload ~/Library/LaunchAgents/ai.bilbao.verificador-pendientes.plist
# o, en Linux:
crontab -l | grep -v verificador-juris-bilbao | crontab -
```
