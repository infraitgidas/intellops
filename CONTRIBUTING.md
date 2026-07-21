# Contributing a IntellOps

¡Gracias por tu interés en contribuir a IntellOps! Somos un proyecto de investigación, desarrollo e innovación (PI+D+i) del grupo GIDAS en UTN FrLP.

Este documento establece las pautas para contribuir de manera efectiva y consistente.

## Índice

1. [Código de Conducta](#código-de-conducta)
2. [¿Cómo Contribuir?](#cómo-contribuir)
3. [Flujo de Trabajo SDD](#flujo-de-trabajo-sdd)
4. [Estructura del Repositorio](#estructura-del-repositorio)
5. [Estándares de Código](#estándares-de-código)
6. [Testing](#testing)
7. [Pull Requests](#pull-requests)
8. [Documentación](#documentación)
9. [Reportar Issues](#reportar-issues)
10. [Publicación Científica](#publicación-científica)

## Código de Conducta

Este proyecto sigue un [Código de Conducta](CODE_OF_CONDUCT.md) exigente. Al participar, se espera que mantengas estos estándares.

## ¿Cómo Contribuir?

### Para estudiantes de Práctica Supervisada (PS)

1. Lee el [Plan de Trabajo](https://github.com/gidas/intellops/wiki/planes-de-trabajo) de tu módulo.
2. Seguí el [Onboarding](onboarding/README.md) para configurar tu entorno.
3. Identificá un cambio en tu módulo y creá un issue siguiendo el template.
4. Seguí el flujo SDD (abajo) para cada cambio.

### Para investigadores/docentes

1. Revisá los [experimentos activos](ml/experiments/) y el [research log](docs/research/RESEARCH.md).
2. Abrí un Discussion para propuestas de investigación.
3. Los datasets y experimentos siguen principios FAIR — pedí acceso via issue.

### Para la comunidad open-source

1. Revisá las [issues abiertas](https://github.com/gidas/intellops/issues) con label `good-first-issue`.
2. Hacé fork del repo, seguí el flujo SDD para tu cambio.
3. Abrí un PR y referenciá la issue correspondiente.

## Flujo de Trabajo SDD

IntellOps usa **Spec-Driven Development (SDD)** con OpenSpec. Cada cambio sigue este flujo:

```
1. IDEA → Issue/Proposal (¿qué problema resuelve?)
2. EXPLORE → Análisis del problema, contexto, alternativas
3. SPEC → Especificación detallada con escenarios Given/When/Then
4. DESIGN → Arquitectura, decisiones (ADR), diagramas
5. TASKS → Breakdown en tareas implementables
6. APPLY → Código + tests (TDD: Red-Green-Refactor)
7. VERIFY → Validación contra specs + revisión por pares
8. ARCHIVE → Merge a develop, ADR final, changelog
```

Cada paso produce un artefacto en `openspec/changes/<change-name>/`.

**Importante**: No se escribe código sin una spec aprobada primero. El contrato (OpenAPI/AsyncAPI) se valida en CI antes del merge.

## Estructura del Repositorio

```
observabilidad/
├── openspec/           ← Artefactos SDD (config, specs, cambios activos/archivados)
├── docs/
│   ├── adr/            ← Architecture Decision Records (formato Nygard)
│   ├── research/       ← Notas científicas, hipótesis, metodología
│   └── divulgation/    ← Notas de divulgación para público general
├── onboarding/         ← Guías de onboarding para nuevos miembros
├── governance/         ← SBOM, compliance, continuidad
├── src/                ← Código fuente del sistema
├── ml/                 ← Experimentos, modelos, datasets
│   ├── experiments/    ← MLflow runs
│   ├── models/         ← Modelos entrenados
│   └── data/           ← Datasets (versionados con DVC)
├── scripts/            ← Scripts de automatización
├── tests/              ← Suites de pruebas
├── TEAM_CHARTER.md     ← Carta del equipo
├── CONTRIBUTING.md     ← Esta guía
├── CODE_OF_CONDUCT.md  ← Código de conducta
└── CHANGELOG.md        ← Registro de cambios por versión
```

## Estándares de Código

### Python (Backend + ML)

- **Estilo**: PEP 8 — verificado con `flake8` y `pylint`
- **Tipos**: Type hints en todas las funciones públicas
- **Docstrings**: Google style para módulos, clases y funciones públicas
- **Formato**: `black` con línea de 88 caracteres (opcional, recomendado)

### JavaScript/TypeScript (Agente RUM + Dashboard)

- **Estilo**: ESLint con configuración estándar
- **Formato**: Prettier
- **Bundle**: < 50KB para agente, < 1MB para dashboard

### OpenAPI / AsyncAPI

- **Contratos**: Siempre versionados, validados en CI
- **Cambios breaking**: Requieren ADR + migración /v2/
- **Ejemplos**: Cada endpoint tiene request/response de ejemplo válido

## Testing

- **Unitario**: `pytest` — todo el código nuevo debe tener tests unitarios
- **Integración**: `pytest + httpx.AsyncClient` — al menos flujo feliz + error
- **Contrato**: `schemathesis` — validación automática contra OpenAPI
- **Carga**: `Locust` o `k6` — para endpoints críticos (ingesta, detección)
- **Cobertura mínima**: 70% en módulos críticos

```bash
# Ejecutar tests
make test

# Test con cobertura
make test-cov

# Test de contrato
make test-contract

# Test de carga
make test-load
```

## Pull Requests

### Template

```markdown
## Descripción
[Contexto del cambio, problema que resuelve]

## Tipo de Cambio
- [ ] Bug fix
- [ ] Nueva feature
- [ ] Refactor
- [ ] Documentación
- [ ] Experimento ML
- [ ] Especificación (spec)

## Spec Link
`openspec/changes/<change-name>/`

## ADR Reference
`docs/adr/XXX-nombre-decision.md`

## Contract Checklist
- [ ] OpenAPI/AsyncAPI actualizado
- [ ] Contract tests pasan
- [ ] Breaking change? → ADR + migración

## ML Metrics (si aplica)
- F1: [valor]
- Recall: [valor]
- Precision: [valor]
- Baseline vs nuevo: [comparación]

## License Scan
- [ ] SBOM actualizado
- [ ] Sin nuevas dependencias restrictivas (SSPL, AGPL)
```

### Review Guidelines

- **Mínimo 2 approvals** para merge a `develop`
- **Mínimo 1 approval** de un maintainer para merge a `main`
- **No self-merge** — incluso el coordinador necesita review
- Los PRs de especificación (spec-only) requieren review del equipo completo

## Convención de commits

El proyecto sigue el estándar **Conventional Commits 1.0.0**.

Formato

tipo(scope) descripción

### Tipos

| Tipo | Descripción |
|-------|-------------|
| feat | Nueva funcionalidad |
| fix | Corrección de errores |
| docs | Documentación |
| refactor | Refactorización sin cambiar comportamiento |
| test | Agregado o modificación de pruebas |
| build | Dependencias o compilación |
| ci | Integración continua |
| chore | Mantenimiento |
| perf | Mejoras de rendimiento |
| style | Cambios de formato |

---

## Scope

El scope representa el **módulo o carpeta principal modificada**.

| Carpeta | Scope |
|----------|-------|
| backend/ | backend |
| frontend/ | frontend |
| collector/ | collector |
| docs/business/ | business |
| docs/research/ | research |
| docs/architecture/ | architecture |
| docs/requirements/ | requirements |
| docs/diagrams/ | diagrams |
| docs/mockups/ | mockups |
| database/ | database |
| docker/ | docker |
| scripts/ | scripts |
| tests/ | tests |
| .github/ | github |
| README.md | readme |
| Configuración global | config |

---

## Ejemplos

feat(frontend) agrega dashboard de observabilidad
feat(backend) implementa endpoint para métricas
fix(database) corrige migración inicial
docs(business) agrega análisis de negocio
docs(research) incorpora estado del arte
docs(architecture) actualiza diagrama C4
docs(requirements) define requerimientos no funcionales
docs(diagrams) agrega diagrama de despliegue
docs(mockups) incorpora prototipos de interfaz
refactor(collector) simplifica procesamiento de eventos
test(frontend) agrega pruebas del dashboard
build(docker) actualiza imagen base
ci(github) agrega workflow de integración continua
docs(readme) actualiza guía de instalación

---

## Flujo de trabajo

1. Actualizar la rama `develop`

git checkout develop
git pull origin develop

2. Crear una rama

git checkout -b feature/dashboard-observabilidad

3. Realizar los cambios

4. Commit

git add .
git commit -m "feat(frontend) agrega dashboard de observabilidad"

5. Subir la rama

git push -u origin feature/dashboard-observabilidad

6. Crear un Pull Request hacia `develop`

7. Luego de la revisión, realizar el merge.

---

## Recomendaciones

- Un commit debe representar un único cambio lógico.
- Utilizar mensajes en presente e infinitivo ("agrega", "corrige", "actualiza").
- Evitar commits genéricos como:
  - "cambios"
  - "update"
  - "fix"
  - "varios"

- Antes de abrir un Pull Request verificar que:
  - El proyecto compila.
  - Las pruebas pasan correctamente.
  - La documentación fue actualizada si corresponde.

## Documentación

Toda documentación sigue estos principios:

1. **Living docs**: La documentación se actualiza en el mismo PR que el código.
2. **Markdown**: Todo en formato Markdown, legible sin renderizar.
3. **Diagramas**: Usar Mermaid (inline en markdown) para diagramas de secuencia, C4, etc.
4. **ADRs**: Toda decisión arquitectónica se documenta en `docs/adr/`.
5. **Onboarding**: Cualquier cambio en el setup se refleja en `onboarding/`.

## Reportar Issues

Usar los templates de issue de GitHub:

- **Bug report**: Pasos para reproducir, comportamiento esperado vs actual, logs, entorno.
- **Feature request**: Problema a resolver, propuesta de solución, alternativas consideradas.
- **Change proposal**: Para cambios SDD formales (sigue el flujo completo).
- **ML experiment**: Hipótesis, métricas target, recursos necesarios.

## Publicación Científica

IntellOps es un proyecto de investigación. Las contribuciones pueden derivar en publicaciones académicas. Si tu contribución es significativa:

1. Coordiná con el equipo para definir autoría.
2. Los experimentos deben ser reproducibles (seed fijo, DVC/MLflow).
3. Los datasets se publican con DOI vía Zenodo/OSF.
4. El paper outline se discute en `docs/research/papers/`.

---

*¿Dudas? Abrí un Discussion en GitHub o contactá al coordinador.*
