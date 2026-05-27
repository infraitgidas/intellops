# Onboarding — Romeo Monfroglio (Módulo ML)

¡Bienvenido al equipo! Este es tu plan de onboarding específico para arrancar con el Módulo de Machine Learning de IntellOps.

## Tu Rol

Diseñar e implementar el **módulo de detección de anomalías** de IntellOps:
- Pipeline de ingesta de métricas de infraestructura
- Modelos ML (Isolation Forest + estadísticos, LSTM como extensión futura)
- Dashboard interactivo con 3 vistas (latencias, heatmap, predicciones)
- Integración con el backend FastAPI

## Tus Primeros Pasos

### Semana 1 — Conocé el Proyecto (días 1-3)

- [ ] Aceptá la invitación de GitHub: https://github.com/infraitgidas/intellops/invitations
- [ ] Cloná el repo y seguí el [onboarding general](README.md)
- [ ] Leé estos documentos en orden:
  1. `TEAM_CHARTER.md` — conocé al equipo y los valores
  2. `docs/brief-v2.md` — contexto completo del proyecto (prestá atención a las secciones de ML)
  3. `openspec/specs/research/state-of-the-art.md` — estado del arte en AIOps y ML para observabilidad
  4. `openspec/specs/research/hypotheses.md` — línea L1 (tu hipótesis de investigación)
  5. `openspec/specs/architecture/containers.md` — ML Engine, LLM, RAG
  6. `openspec/specs/benchmarking.md` — cómo vamos a evaluar los modelos
- [ ] Ejecutá `make setup` y `make up` para ver el API funcionando
- [ ] Corré `make test` — todo verde ✅

### Semana 1 — Investigación Técnica (días 4-5)

- [ ] Instalá scikit-learn localmente: `pip install scikit-learn pandas matplotlib`
- [ ] Ejecutá un Isolation Forest de ejemplo con datos sintéticos
- [ ] Investigá: ¿qué es OpenTelemetry? ¿cómo se instrumenta un servicio?
- [ ] Leé sobre FastAPI — cómo crear endpoints, validación con Pydantic
- [ ] Anotá preguntas para la daily del equipo

### Semana 2 — Primer Cambio SDD

Tu primer cambio va a ser: **crear el esqueleto del ML Engine con un detector de ejemplo**.

Seguí el flujo SDD:

```bash
# 1. Creá un issue de tipo "Change Proposal"
#    https://github.com/infraitgidas/intellops/issues/new?template=02-change-proposal.md
#    Título: "[change] esqueleto-ml-engine"

# 2. Esperá la review del coordinador

# 3. Cuando esté aprobado, creá tu rama
git checkout develop
git pull origin develop
git checkout -b feat/ml-engine-skeleton develop

# 4. Implementá
#    - Estructura de src/ml/ con detector base
#    - Tests unitarios del detector
#    - Endpoint POST /ml/detect en el backend

# 5. PR a develop
git add -A
git commit -m "feat: esqueleto ML Engine con detector base"
git push origin feat/ml-engine-skeleton
# Abrí PR en GitHub con el template
```

## Documentos Clave para tu Módulo

| Documento | Por qué es importante |
|-----------|----------------------|
| `openspec/specs/research/hypotheses.md` (H1) | Tu hipótesis con criterios de validación |
| `openspec/specs/research/benchmarking.md` (sección 2.2) | Benchmark de modelos ML que vas a implementar |
| `openspec/specs/research/experiments.md` (EXP-001 a 004) | Tus experimentos planificados |
| `openspec/specs/architecture/components.md` | Estructura de componentes del ML Engine |
| `openspec/specs/architecture/interfaces.md` | API del ML Engine |
| `openspec/specs/architecture/containers.md` | Footprint y recursos del ML Engine |

## Stack Específico

| Herramienta | Propósito | Estado |
|-------------|-----------|--------|
| Python + scikit-learn | Modelos ML | Listo |
| FastAPI | Backend API | Listo (esqueleto) |
| SQLite | Almacenamiento de métricas | Por implementar |
| DVC | Versionado de datasets | Por configurar |
| MLflow | Tracking de experimentos | Por configurar |
| Evidently | Drift monitoring | Por configurar |
| React + D3.js | Dashboard (3 vistas) | Por implementar |

## Referencias Rápidas

- [scikit-learn Isolation Forest](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.IsolationForest.html)
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [OpenTelemetry Python](https://opentelemetry.io/docs/languages/python/)
- [DVC Documentation](https://dvc.org/doc)
- [MLflow Documentation](https://mlflow.org/docs/latest/index.html)
- [D3.js](https://d3js.org/)

## Checklist de Avance

- [ ] Semana 1: Onboarding completo + lectura de docs
- [ ] Semana 2: Esqueleto ML Engine (primer cambio SDD)
- [ ] Semana 10: Revisión Hito 50%
- [ ] Semana 14: MVP-1 con ML + Dashboard + GenIA
- [ ] Semana 18: Prototipo funcional completo
- [ ] Semana 20: Informe Final + Paper JAIIO/CACIC

---

*¿Dudas? Abrí un issue con label `setup` o hablá con el coordinador.*
