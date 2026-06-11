# Onboarding — Santiago Montanari

¡Bienvenido al equipo! Este onboarding tiene **dos fases** secuenciales: primero construís los fundamentos de calidad y automatización de infraestructura, y después aplicás ese conocimiento a la **observability-driven QA**: calidad de software medida con señales de experiencia de usuario real.

---

## Fase 1: Fundamentos de Infra (Sprint 1-2)

Diseñar e implementar el **módulo de QA** de IntellOps sobre el pipeline de desarrollo.

### Tu Rol en Fase 1

- Suite de pruebas automatizadas (unitarias, integración, E2E)
- Pipeline CI/CD en GitHub Actions con quality gates
- Entornos de testing reproducibles con Docker Compose
- Informe de rendimiento del sistema

### Semana 1 — Conocé el Proyecto (días 1-3)

- [ ] Aceptá la invitación de GitHub: https://github.com/infraitgidas/intellops/invitations
- [ ] Cloná el repo y seguí el [onboarding general](README.md)
- [ ] Leé estos documentos en orden:
  1. `TEAM_CHARTER.md` — conocé al equipo y los valores
  2. `docs/brief-v2.md` — contexto completo del proyecto
  3. `openspec/specs/research/hypotheses.md` — línea L4 (tu hipótesis de Fase 1)
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

### Documentos Clave para Fase 1

| Documento | Por qué es importante |
|-----------|----------------------|
| `openspec/specs/research/hypotheses.md` (H4) | Tu hipótesis de Fase 1 con criterios de validación |
| `openspec/specs/research/experiments.md` (EXP-301 a 303) | Tus experimentos de Fase 1 planificados |
| `openspec/specs/architecture/quality-attributes.md` | Los 13 escenarios QA que vas a validar |
| `openspec/specs/architecture/constraints.md` | Restricciones de proceso y metodología |
| `CONTRIBUTING.md` | Estándares de testing y PR |
| `.github/workflows/ci.yml` | Template del CI que vas a implementar |
| `.github/PULL_REQUEST_TEMPLATE.md` | Template que los demás van a usar gracias a vos |

### Stack Específico — Fase 1

| Herramienta | Propósito | Estado |
|-------------|-----------|--------|
| pytest + pytest-cov | Tests unitarios y cobertura | Listo (esqueleto) |
| flake8 + pylint | Linters | Listo (esqueleto) |
| GitHub Actions | CI/CD | Template listo, implementar |
| schemathesis | Contract testing | Por implementar |
| k6 / Locust | Pruebas de carga | Por implementar |
| Docker Compose | Entornos de testing | Listo (esqueleto) |

---

## Fase 2: Observability-Driven QA (Sprint 3+)

Una vez que tenés el pipeline CI/CD funcionando y entendés cómo se prueba un sistema, pasamos al siguiente nivel: **usar señales de OpenTelemetry como quality gates** para detectar regresiones de experiencia de usuario antes de hacer deploy.

### Tu Rol en Fase 2

| Actividad I+D+i | Por qué es investigación | Qué vas a construir |
|----------------|-------------------------|---------------------|
| **Observability-driven testing** | Usar señales de OTel como quality gates en CI/CD es un área emergente (no hay herramientas maduras open-source) | Pipeline CI que corre tests con OTel instrumentado y valida trazas + métricas como parte del quality gate |
| **Synthetic user journeys con trazabilidad OTel** | Simular usuarios reales con trazas completas validadas contra Tempo es un desafío de diseño | Scripts de tráfico sintético (Locust) con contexto OTel propagation |
| **Chaos Engineering para UX** | Inyectar latencia/errores y medir impacto real en UX metrics es investigación activa en SRE | Experimentos de caos controlados con validación de User Health Score |
| **CBA de observabilidad** | Cuantificar el retorno de inversión en observabilidad en contexto académico es único | Dashboard de costos vs incidentes evitados, métricas de efectividad de alertas |

### Semana 3-4 — Investigación y Prototipado

- [ ] Leé la especificación H7 en `openspec/specs/research/hypotheses.md`
- [ ] Revisá los experimentos EXP-QA-01 a 04 en `openspec/specs/research/experiments.md`
- [ ] Investigá cómo instrumentar Locust con OpenTelemetry para generar trazas
- [ ] Armá un PoC de un synthetic journey que genere una traza completa validable en Tempo
- [ ] Investigá chaos engineering tools: Chaos Mesh, Litmus, o algo más liviano
- [ ] Diseñá la estructura de un quality gate OTel-based: ¿qué métricas? ¿qué thresholds?

### Semana 5+ — Implementación

```bash
# Primer cambio SDD de Fase 2
# Título: "[change] quality-gates-otel"
git checkout -b feat/quality-gates-otel develop

# Implementación:
# - tests/synthetic/journeys.py — Synthetic user journeys con OTel
# - .github/workflows/ci.yml — Quality gates OTel agregados
# - tests/chaos/ — Experimentos de caos controlados
# - docs/research/cba-observabilidad.md — CBA del stack
```

### Documentos Clave para Fase 2

| Documento | Por qué es importante |
|-----------|----------------------|
| `openspec/specs/research/hypotheses.md` (H7) | Tu hipótesis de Fase 2 |
| `openspec/specs/research/experiments.md` (EXP-QA-*) | Tus experimentos de QA con OTel |
| `openspec/specs/architecture/quality-attributes.md` | Nuevos escenarios QA basados en OTel |
| `.github/workflows/ci.yml` | Pipeline CI que vas a extender con gates OTel |

### Stack Específico — Fase 2

| Herramienta | Propósito | Estado |
|-------------|-----------|--------|
| Locust + OTel | Synthetic user journeys con trazas | Investigar |
| Tempo | Validación de trazas completas en CI | Por configurar |
| Chaos Mesh / Litmus | Experimentos de caos controlados | Investigar |
| OpenTelemetry Collector | Recepción de trazas del synthetic testing | Por configurar |
| Grafana | Dashboard de CBAs y calidad | Por configurar |

### Referencias Rápidas

#### Fase 1
- [pytest Documentation](https://docs.pytest.org/)
- [GitHub Actions Docs](https://docs.github.com/en/actions)
- [schemathesis](https://schemathesis.readthedocs.io/)
- [k6 Documentation](https://k6.io/docs/)
- [Locust Documentation](https://docs.locust.io/)
- [pytest-cov](https://pytest-cov.readthedocs.io/)

#### Fase 2
- [OpenTelemetry Python](https://opentelemetry.io/docs/languages/python/)
- [Locust + OTel instrumentation](https://docs.locust.io/en/stable/extending-locust.html)
- [Grafana Tempo](https://grafana.com/docs/tempo/latest/)
- [Chaos Mesh](https://chaos-mesh.org/)
- [Litmus Chaos](https://litmuschaos.io/)

### Checklist de Avance

#### Fase 1
- [ ] Semana 1: Onboarding completo + lectura de docs
- [ ] Semana 2: Pipeline CI real funcionando (primer cambio SDD)
- [ ] Semana 5: Informe Parcial 1 (baseline calidad + ADRs QA)
- [ ] Semana 11: Tests unitarios >= 70% (Hito 50%)

#### Fase 2
- [ ] Semana 3-4: PoC synthetic journey OTel funcionando con validación en Tempo
- [ ] Semana 5-6: Quality gates OTel en CI/CD (primer cambio SDD Fase 2)
- [ ] Semana 8-9: Dashboard de CBAs de observabilidad publicado
- [ ] Semana 15: Chaos experiments controlados integrados
- [ ] Semana 19: Quality gates OTel + informe de rendimiento completo
- [ ] Semana 20: Informe Final + Paper JAIIO/CACIC

---

*¿Dudas? Abrí un issue con label `setup` o hablá con el coordinador.*
