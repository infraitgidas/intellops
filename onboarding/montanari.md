# Onboarding — Santiago Montanari (Módulo QA)

¡Bienvenido al equipo! Este es tu plan de onboarding específico para arrancar con el Módulo de Aseguramiento de Calidad de IntellOps.

## Tu Rol

Diseñar e implementar el **módulo de QA** de IntellOps:
- Suite de pruebas automatizadas (unitarias, integración, E2E)
- Pipeline CI/CD en GitHub Actions con quality gates
- Entornos de testing reproducibles con Docker Compose
- Informe de rendimiento del sistema

## Tus Primeros Pasos

### Semana 1 — Conocé el Proyecto (días 1-3)

- [ ] Aceptá la invitación de GitHub: https://github.com/infraitgidas/intellops/invitations
- [ ] Cloná el repo y seguí el [onboarding general](README.md)
- [ ] Leé estos documentos en orden:
  1. `TEAM_CHARTER.md` — conocé al equipo y los valores
  2. `docs/brief-v2.md` — contexto completo del proyecto
  3. `openspec/specs/research/hypotheses.md` — línea L4 (tu hipótesis de investigación)
  4. `openspec/specs/architecture/quality-attributes.md` — atributos de calidad que vas a validar
  5. `openspec/specs/architecture/constraints.md` — restricciones técnicas que afectan testing
  6. `CONTRIBUTING.md` — flujo SDD y estándares de testing
- [ ] Ejecutá `make setup` y `make up` para ver el API funcionando
- [ ] Corré `make test` — todo verde ✅
- [ ] Corré `make lint` — entendé cómo funciona el linter

### Semana 1 — Investigación Técnica (días 4-5)

- [ ] Experimentá con pytest: escribí un test adicional en `tests/`
- [ ] Investigá: ¿qué es contract testing? ¿cómo funciona schemathesis?
- [ ] Leé sobre GitHub Actions — estructura de workflows, jobs, steps
- [ ] Probá k6 o Locust localmente para entender pruebas de carga
- [ ] Anotá preguntas para la daily del equipo

### Semana 2 — Primer Cambio SDD

Tu primer cambio va a ser: **implementar el pipeline CI/CD real con quality gates**.

El CI ya tiene un template en `.github/workflows/ci.yml`. Tu trabajo es hacerlo funcionar de verdad.

Seguí el flujo SDD:

```bash
# 1. Creá un issue de tipo "Change Proposal"
#    https://github.com/infraitgidas/intellops/issues/new?template=02-change-proposal.md
#    Título: "[change] pipeline-ci-real"

# 2. Esperá la review del coordinador

# 3. Cuando esté aprobado, creá tu rama
git checkout develop
git pull origin develop
git checkout -b feat/pipeline-ci-real develop

# 4. Implementá
#    - Hacer que el CI workflow de .github/workflows/ci.yml funcione de verdad
#    - Agregar quality gates (coverage threshold, lint score)
#    - Agregar contract testing con schemathesis
#    - Tests de carga con k6 (opcional en este primer cambio)

# 5. PR a develop
git add -A
git commit -m "feat: pipeline CI real con quality gates"
git push origin feat/pipeline-ci-real
# Abrí PR en GitHub con el template
```

## Documentos Clave para tu Módulo

| Documento | Por qué es importante |
|-----------|----------------------|
| `openspec/specs/research/hypotheses.md` (H4) | Tu hipótesis con criterios de validación |
| `openspec/specs/research/experiments.md` (EXP-301 a 303) | Tus experimentos planificados |
| `openspec/specs/architecture/quality-attributes.md` | Los 13 escenarios QA que vas a validar |
| `openspec/specs/architecture/constraints.md` | Restricciones de proceso y metodología |
| `CONTRIBUTING.md` | Estándares de testing y PR |
| `.github/workflows/ci.yml` | Template del CI que vas a implementar |
| `.github/PULL_REQUEST_TEMPLATE.md` | Template que los demás van a usar gracias a vos |
| `openspec/config.yaml` (sección testing) | Testing capabilities definidas |

## Stack Específico

| Herramienta | Propósito | Estado |
|-------------|-----------|--------|
| pytest + pytest-cov | Tests unitarios y cobertura | Listo (esqueleto) |
| flake8 + pylint | Linters | Listo (esqueleto) |
| GitHub Actions | CI/CD | Template listo, implementar |
| schemathesis | Contract testing | Por implementar |
| k6 / Locust | Pruebas de carga | Por implementar |
| Docker Compose | Entornos de testing | Listo (esqueleto) |

## Referencias Rápidas

- [pytest Documentation](https://docs.pytest.org/)
- [GitHub Actions Docs](https://docs.github.com/en/actions)
- [schemathesis](https://schemathesis.readthedocs.io/)
- [k6 Documentation](https://k6.io/docs/)
- [Locust Documentation](https://docs.locust.io/)
- [pytest-cov](https://pytest-cov.readthedocs.io/)

## Checklist de Avance

- [ ] Semana 1: Onboarding completo + lectura de docs
- [ ] Semana 2: Pipeline CI real funcionando (primer cambio SDD)
- [ ] Semana 5: Informe Parcial 1 (baseline calidad + ADRs QA)
- [ ] Semana 11: Tests unitarios >= 70% (Hito 50%)
- [ ] Semana 15: Contract testing + E2E
- [ ] Semana 19: Quality gates + informe rendimiento
- [ ] Semana 20: Informe Final + Paper JAIIO/CACIC

---

*¿Dudas? Abrí un issue con label `setup` o hablá con el coordinador.*
