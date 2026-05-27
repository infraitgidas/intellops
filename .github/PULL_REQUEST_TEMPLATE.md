---
name: Pull Request
about: Template SDD para cambios en IntellOps
title: "[tipo] descripción breve"
---

## Descripción

<!-- Contexto del cambio, problema que resuelve, motivación -->

## Tipo de Cambio

- [ ] Bug fix
- [ ] Nueva feature
- [ ] Refactor
- [ ] Documentación
- [ ] Experimento ML
- [ ] Especificación (spec)
- [ ] Infraestructura / CI

## Spec Link

`openspec/changes/<change-name>/`

## ADR Reference

`docs/adr/NNNN-titulo.md`

## Contract Checklist

- [ ] OpenAPI/AsyncAPI actualizado
- [ ] Contract tests pasan
- [ ] Breaking change? → ADR + versión nueva

## Test Checklist

- [ ] Tests unitarios agregados/actualizados
- [ ] Tests de integración pasan
- [ ] Contract tests pasan
- [ ] Cobertura >= 70%

## ML Metrics (si aplica)

| Métrica | Valor | Baseline | Δ |
|---------|-------|----------|---|
| F1 | — | — | — |
| Recall | — | — | — |
| Precision | — | — | — |

## License Scan

- [ ] SBOM actualizado
- [ ] Sin nuevas dependencias restrictivas (SSPL, AGPL)
- [ ] Dependencias agregadas tienen licencia compatible Apache-2.0/MIT

## Documentación

- [ ] Changelog actualizado
- [ ] Onboarding actualizado (si cambia setup)
- [ ] ADR creado (si es decisión arquitectónica)

## Self-Review

- [ ] Código revisado por mí mismo
- [ ] No hay secretos, tokens o credenciales en el código
- [ ] Los mensajes de commit siguen Conventional Commits
