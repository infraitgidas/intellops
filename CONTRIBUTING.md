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
- **Bundle del agente RUM**: ≤ 30 KB gzip, objetivo 20 KB
  (`docs/architecture/ContratoAgenteRUM.md` §10); el dashboard, < 1 MB
- **Dependencias de runtime del agente**: ninguna; `esbuild` es la única
  dependencia de desarrollo (`src/agent/package.json`)

### Agente RUM (`src/agent/`)

```bash
cd src/agent
npm install
npm run build       # genera dist/rum.js (minificado) y verifica el tope gzip
npm test            # tests del agente con el runner nativo de Node
```

La verificación contra una ingesta real se hace con `scripts/e2e.mjs`
(ver `src/agent/README.md`). La API key se pasa por variable de entorno:
nunca se versiona.

### OpenAPI / AsyncAPI

- **Contratos**: Siempre versionados, validados en CI
- **Cambios breaking**: Requieren ADR + migración /v2/
- **Ejemplos**: Cada endpoint tiene request/response de ejemplo válido

## Testing

- **Unitario**: `pytest` — todo el código nuevo debe tener tests unitarios
- **Integración**: `pytest + httpx.AsyncClient` — al menos flujo feliz + error
- **Contrato**: `schemathesis` — validación automática contra OpenAPI
- **Carga**: `Locust` o `k6` — para endpoints críticos (ingesta, detección)
- **Cobertura mínima**: 70% (gate único en `[tool.coverage.report] fail_under` de `pyproject.toml`, y `--cov-fail-under=70` en el CI: por debajo de ese valor el job falla)

### Capas: `unit` vs `integration`

Cada test se clasifica automáticamente (`tests/conftest.py`):

- **`integration`**: usa algún fixture de base de datos (`db_session`, `client`, `make_admin`, `seed_admin`, `alembic_cfg`, `conn`, …). Requiere Postgres migrado.
- **`unit`**: todo lo demás. Corre **sin** Postgres.

Si un test toca la DB sin pedir esos fixtures (p. ej. vía el engine global, como `/health`), marcalo con `@pytest.mark.integration`; de lo contrario fallará en el job `Unit Tests` del CI, que no tiene base de datos.

### Entorno reproducible de testing

Toda la suite corre en contenedores (`Dockerfile.test` + `docker-compose.test.yml`), así que el único requisito en la máquina es Docker con Compose v2 y `make` (tu laptop —x86_64 o ARM—, el servidor del laboratorio o el runner del CI dan el mismo resultado):

- **Dependencias fijadas**: `requirements/dev.lock` (runtime + dev, con hashes) se instala en la imagen y en los jobs del CI. Si agregás o cambiás una dependencia en `pyproject.toml`, corré `make lock` (requiere [uv](https://docs.astral.sh/uv/); el target usa la versión fijada en `UV_VERSION`, la misma del CI) y commiteá el lock; el CI falla si quedó desactualizado. El lock trae hashes para x86_64 y ARM.
- **Versiones mayores deliberadas**: el lock fija lo que `>=` resolvía al crearlo (p. ej. pylint 4, SQLAlchemy 2.1, pytest 9). Subir de versión es una decisión explícita: `make lock UV_FLAGS=--upgrade`, revisar el diff y que el CI quede en verde.
- **Postgres efímero**: `test-db` vive en tmpfs y en un proyecto Compose aparte (`intellops-test`); no toca la DB de `make up` ni publica puertos.
- **Código montado**: el repo se monta en `/app`, no hace falta reconstruir la imagen al cambiar código. Los reportes (`coverage.xml`, `htmlcov/`, `reports/junit.xml`) quedan en el repo con tu usuario.
- **Variables fijas**: `DATABASE_URL`, `JWT_SECRET` y `ADMIN_BOOTSTRAP_PASSWORD` vienen del compose; un `.env` local no cambia el resultado.

```bash
make ci                 # lo mismo que el CI: lint → unit → migraciones → suite + cobertura (≥70%)
make test               # suite completa
make test-unit          # solo unit (sin DB, segundos)
make test-integration   # solo integración (Postgres)
make test-cov           # suite con cobertura (HTML en htmlcov/)
make test-contract      # contract tests (schemathesis, OpenAPI 3.1)
make lint               # flake8 (0 hallazgos) + pylint --fail-on=W,E (≥ 9.0)
make smoke              # smoke E2E: stack real + stub de Telegram (docs/operations/smoke-e2e.md)
make test-down          # borra contenedores y DB efímera
```

Evitá `sudo make ci`: con sudo el UID es 0 y los reportes quedan de root. Si tu usuario no tiene acceso al socket de Docker, pedí que lo agreguen al grupo `docker`.

```bash

# Comando puntual dentro del entorno (exportá tu UID/GID para que los
# archivos generados queden a tu nombre; `make` lo hace solo)
HOST_UID=$(id -u) HOST_GID=$(id -g) \
  docker compose -f docker-compose.test.yml run --rm tests pytest tests/test_auth.py -k login
```

### Pipeline de CI (`.github/workflows/ci.yml`)

Corre en push a `main`/`develop`, en PRs hacia esas ramas y manualmente (`workflow_dispatch`). Un push nuevo cancela la corrida anterior de la misma rama.

| Job | Qué valida | Falla si |
|-----|-----------|----------|
| `Lint & Format` | `flake8 src/ tests/` + `pylint src/ --fail-under=9.0 --fail-on=W,E` | hay un warning o error de flake8, un warning o error de pylint, o el score < 9.0 |
| `Unit Tests` | `pytest -m unit` sin Postgres | falla un test unitario |
| `Unit & Integration Tests` | suite completa contra Postgres 16 + cobertura | falla un test o la cobertura < 70% |
| `Reproducible Test Env (Docker)` | `make lock` sin diff + `make ci` en el entorno de testing | el lock está desactualizado o falla el pipeline en el contenedor |
| `Contract Tests` | `tests/test_contract.py` (schemathesis, OpenAPI 3.1) | el contrato no valida |
| `License Scan & SBOM` | SBOM CycloneDX + `pip-licenses` | hay dependencias SSPL/AGPL |
| `Docker Build` | `docker compose build` | la imagen no construye |

### Gates bloqueantes

Cuatro gates **rompen el job** (no hay `continue-on-error` en ningún job ni
step): un check en rojo no se puede mergear.

| Gate | Job | Umbral / condición | Qué lo dispara |
|------|-----|--------------------|----------------|
| Cobertura (S11, #71) | `Unit & Integration Tests` | `--cov-fail-under=70` (y `fail_under = 70` en `pyproject.toml`) | la suite pasa pero el total de `src/` queda por debajo de 70% |
| Lint (S12, #71) | `Lint & Format` | `flake8` sin hallazgos + `pylint --fail-under=9.0 --fail-on=W,E` | cualquier warning o error de flake8 o de pylint, o score < 9.0 |
| Contrato (S13, #71) | `Contract Tests` | `pytest tests/test_contract.py` (aserciones estructurales + schemathesis) | el `openapi.yaml` no carga, pierde un path/schema/status esperado o una respuesta no valida |
| Frontend (S16/S17/S19, #69) | `Frontend (SPA)` | `npm ci` + lint + `vitest` + build + `check-size` (< 1 MB) + smoke E2E | un warning de eslint, un test rojo, un `dist/` de más de 1 MB o un smoke E2E fallido |

`Docker Build` depende de `Lint & Format`, `Unit & Integration Tests` y
`Contract Tests`: si un gate falla, el flujo no llega a construir la imagen.
Los umbrales están fijados por `tests/test_ci_gates.py`, que lee este workflow
y falla si alguien los baja o agrega `continue-on-error`.

### Frontend (SPA React, `src/frontend/`)

La SPA de B.5 (latencias RUM + heatmap UX) es un **build estático**, no un
contenedor del compose (ADR-0010). Corre en el host con Node ≥ 22
(`src/frontend/.nvmrc`), no en el contenedor de testing.

```bash
cd src/frontend
npm ci                # instala exactamente el package-lock.json (S16)
npm run lint          # eslint, 0 warnings
npm test              # Vitest + Testing Library (componentes y hooks)
npm run build         # tsc --noEmit + vite build → dist/
npm run check-size    # gate S17: dist/ < 1 MB (raw) e informa gzip
npm run test:e2e      # Playwright: stub de API + vite preview del build
```

Desde el root: `make fe-install`, `make fe-lint`, `make fe-test`,
`make fe-build` (build + tamaño) y `make fe-e2e`.

- **Job `frontend` del CI**: `npm ci` → lint → tests → build → `check-size` →
  `npx playwright install --with-deps chromium` → `test:e2e`, todo bloqueante
  (QF-1). Presupuesto actual: ~243 kB raw / ~75 kB gzip (tope 1 MB).
- **Smoke E2E sin navegador propio**: si la revisión de Chromium del caché no
  coincide con la de `@playwright/test`, usá
  `PLAYWRIGHT_CHROMIUM_PATH=/usr/bin/chromium npm run test:e2e`.
- **Autenticación (D2)**: `/metrics/*` exige `X-API-Key`, así que la key la pega
  el operador en la UI y vive **sólo** en `sessionStorage`; nunca va al bundle,
  a la URL, a `localStorage` ni a los logs. Un 401/403 la descarta. Es una
  herramienta interna: la deuda con dueño es un endpoint de lectura con JWT
  (`require_role`), que es backend nuevo y sale de B.5.
- **Qué mide el heatmap (D3)**: la API pública no expone `page_url` ni
  `metadata`, así que el mapa es tiempo × métrica (AVG por bucket, normalizado
  por fila) con tabla accesible; no es una grilla página × posición.

#### Reproducir cada fallo localmente

Mismo entorno que el CI (contenedor `tests` de `docker-compose.test.yml`):

```bash
# 1. Lint (S12): un warning de flake8 y uno de pylint rompen el job.
#    flake8 sale con código 1 ante cualquier hallazgo; pylint, con
#    --fail-on=W,E, también falla con un solo warning (--fail-under solo no
#    alcanza porque un warning deja el score en 9.9x).
docker compose -f docker-compose.test.yml run --rm --no-deps tests sh -c \
  'printf "import os\n" > /tmp/warn.py && flake8 /tmp/warn.py'; echo "exit=$?"
docker compose -f docker-compose.test.yml run --rm --no-deps tests sh -c \
  'printf "import os\n" > /tmp/warn.py && pylint /tmp/warn.py --fail-on=W,E'; echo "exit=$?"

# 2. Cobertura (S11): subí el umbral por encima del real y mirá el fallo.
make test-cov                                                              # pasa (gate 70%)
docker compose -f docker-compose.test.yml run --rm tests sh -c \
  'alembic upgrade head && pytest --cov --cov-fail-under=99 -q'; echo "exit=$?"
# → "Required test coverage of 99.0% not reached. Total coverage: <real>%" y exit 1

# 3. Contrato (S13): rompé el spec en una copia y corré el mismo test.
cp openspec/specs/openapi.yaml /tmp/openapi-broken.yaml
$EDITOR /tmp/openapi-broken.yaml        # p. ej. borrá `security` de /telemetry/metrics
docker compose -f docker-compose.test.yml run --rm \
  -v /tmp/openapi-broken.yaml:/app/openspec/specs/openapi.yaml tests \
  sh -c 'alembic upgrade head && pytest tests/test_contract.py -q'; echo "exit=$?"
```

**Calibración de pylint (S12)**: el gate corre sin `--disable` y sin mensajes
desactivados en `pyproject.toml`: con las versiones fijadas en
`requirements/dev.lock` (pylint 4.1.3 / astroid 4.3.4) el árbol pasa con **0
warnings y 0 errores**. Las dos correcciones que hicieron falta son de código,
no de configuración:

- `src/api/presentation/routers/metrics.py`: `GET /metrics/list` es un catálogo
  global, así que el parámetro que `Depends(require_api_key)` consume sin uso se
  llama `_application`. W0613 sigue activo en todo el resto del repo.
- Los imports `src.ml.*` pasaron a `ml.*` (como `api.*` y el resto del repo):
  cargaban el mismo archivo como dos módulos distintos (`src.ml.schemas` y
  `ml.schemas` → dos clases `MetricBatchInput`), lo que rompía `isinstance`
  entre el loader del dataset y los tests, y no resolvían con el
  `PYTHONPATH=/app/src` de las imágenes.

Corré los linters en el entorno fijado (`make lint`), no en un venv propio: con
`astroid` viejo (4.0.x) aparecen falsos positivos de pydantic (`E1101` sobre
`FieldInfo.startswith`) que el lock ya no reporta.

**Reporte de cobertura**: en la pestaña *Actions* de cada corrida, el resumen del job `Unit & Integration Tests` muestra el total y la tabla por archivo; el artefacto `coverage-report` trae `coverage.xml`, el HTML navegable (`htmlcov/index.html`) y `reports/junit.xml`.

Reproducir el CI localmente sin Docker (con Python 3.11 y un Postgres accesible en `DATABASE_URL`):

```bash
pip install --require-hashes -r requirements/dev.lock && pip install --no-deps -e .
flake8 src/ tests/ && pylint src/ --fail-under=9.0 --fail-on=W,E
PYTHONPATH=. pytest -m unit
alembic upgrade head && PYTHONPATH=. pytest --cov --cov-fail-under=70 --cov-report=term-missing
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
