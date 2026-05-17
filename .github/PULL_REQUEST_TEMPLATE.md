# Pull request

## Qué cambia

<!-- Resumen de una línea de los cambios -->

## Por qué

<!-- El problema que motiva el cambio. Si hay issue relacionado, enlázalo: closes #123 -->

## Tipo de cambio

- [ ] Bug fix (cambio que arregla un comportamiento incorrecto)
- [ ] Nueva feature (cambio que añade funcionalidad)
- [ ] Cambio en system prompt de agente (impacta calidad de verificación)
- [ ] Refactor (mejora de código sin cambio funcional)
- [ ] Documentación
- [ ] Tests

## Tests

- [ ] He añadido tests que cubren el cambio
- [ ] Los 26 tests offline existentes siguen pasando (`pytest pruebas/ -v`)
- [ ] Si he tocado prompts de agentes, he ejecutado un test E2E real y adjunto el `informe-<sid>.md` resultante

## Checklist

- [ ] He leído [CONTRIBUTING.md](../CONTRIBUTING.md)
- [ ] He añadido entrada en `CHANGELOG.md` bajo `[Unreleased]`
- [ ] El código sigue PEP 8 / Black con line-length 88
- [ ] Los commits siguen [Conventional Commits](https://www.conventionalcommits.org/)
- [ ] **No** he subido API keys ni `.env` reales
