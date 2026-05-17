# Contribuir a Verificador Legal

Gracias por interesarte en contribuir. Este proyecto está bajo
**Apache License 2.0** y acepta contribuciones de cualquier persona.

## Antes de empezar

- Lee el [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md). Esperamos comportamiento profesional en todas las interacciones.
- Revisa los [issues abiertos](https://github.com/ricardodevis/verificador-legal/issues). Algo puede estar ya en marcha.
- Para cambios grandes, abre un issue **antes** de empezar a programar, para discutir el enfoque.

## Tipos de contribución valoradas

1. **Reportes de bugs** — usa la plantilla de issue [bug_report](.github/ISSUE_TEMPLATE/bug_report.yml).
2. **Nuevos patrones de extracción de citas** — si tu jurisdicción usa abreviaturas no soportadas, añádelas a `src/skill/verificador-jurisprudencia-es/references/patrones-cita.md` y al script `extraer_citas.py`.
3. **Nuevos boletines autonómicos** — añade el nuevo boletín a `customizar.py` (mapa `JURISDICCIONES_INFO`) y a `customizacion-jurisdicciones.md`.
4. **Tests** — siempre bienvenidos, especialmente tests E2E con mocks.
5. **Documentación** — corrigir typos, ampliar ejemplos, traducir a otros idiomas oficiales del Estado.
6. **Mejoras al sistema de fallback** — si encuentras una fuente oficial alternativa para un tipo de cita, propónla en un issue.

## Flujo de contribución

```bash
# 1. Fork en GitHub
# 2. Clone tu fork
git clone https://github.com/<tu-usuario>/verificador-legal.git
cd verificador-legal

# 3. Crea una rama descriptiva
git checkout -b feat/soporte-bopa-asturias
# o
git checkout -b fix/regex-stsj-andalucia

# 4. Desarrolla y testea
cd src
pip install -r requirements.txt
pytest pruebas/ -v

# 5. Commit con Conventional Commits
git commit -m "feat(extractor): añadir soporte BOPA Asturias"
# o
git commit -m "fix(sub-cendoj): regex STSJ Andalucía ignoraba sufijo Sevilla"

# 6. Push y abre un PR
git push origin feat/soporte-bopa-asturias
```

## Estilo de código

- **Python**: PEP 8 / Black con line-length 88. Usa anotaciones de tipo cuando ayuden a la legibilidad.
- **Markdown**: una idea por párrafo, máximo 80 caracteres por línea cuando sea razonable, listas con `-` (no `*`).
- **Commits**: usa [Conventional Commits](https://www.conventionalcommits.org/) (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`).

## Tests

**Todos los PR deben pasar los 26 tests offline existentes**:

```bash
cd src
pytest pruebas/test_unitarios.py pruebas/test_comportamiento.py -v
```

Si añades funcionalidad, añade tests. Si arreglas un bug, añade un test que cubra el bug.

Los **tests E2E** (que consumen tokens) NO se ejecutan en CI por coste. Si tu cambio afecta al comportamiento de los sub-agentes en producción, descríbelo en el PR y, si tienes credenciales propias, ejecuta el test E2E y adjunta el `informe-<sid>.md` resultante.

## Cambios a system prompts de agentes

Los `prompts/*.md` son el "código de comportamiento" del sistema. Cualquier cambio aquí afecta a la calidad de la verificación. Para cambios en prompts:

1. Explica en el PR **qué problema observado motivó el cambio**.
2. Muestra **antes/después** del comportamiento con ejemplos.
3. Si el cambio es no trivial, ejecuta el test E2E completo y adjunta resultado.
4. Documenta el cambio en `CHANGELOG.md`.

## Documentación

Toda función pública nueva debe llevar docstring. Los cambios significativos deben reflejarse en `docs/`.

## Trato de la API key durante desarrollo

- **Nunca subas `.env` a git** (está en `.gitignore`).
- **Nunca pegues una API key real en issues, PRs ni comentarios**.
- Para tests E2E usa una key dedicada con scope mínimo, y rótala tras usarla.

## Licencia de tus contribuciones

Al enviar un PR, aceptas que tu contribución se licencia bajo
**Apache License 2.0**, los mismos términos que el resto del
proyecto.

## Contacto

Para discusiones de diseño profundas: abre un issue.
Para coordinación de roadmap: ricardo@bilbao.ai.
