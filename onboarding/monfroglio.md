# Onboarding — Romeo Monfroglio

¡Bienvenido al equipo! Este onboarding tiene **dos fases** secuenciales: primero construís los fundamentos de ML sobre infraestructura, y después aplicás ese conocimiento a la observabilidad predictiva centrada en el usuario con agentes de IA.

---

## Fase 1: Fundamentos de Infra (Sprint 1-2)

Diseñar e implementar el **módulo de detección de anomalías** de IntellOps sobre métricas de infraestructura.

### Tu Rol en Fase 1

- Pipeline de ingesta de métricas de infraestructura
- Modelos ML (Isolation Forest + estadísticos, LSTM como extensión futura)
- Dashboard interactivo con 3 vistas (latencias, heatmap, predicciones)
- Integración con el backend FastAPI

### Semana 1 — Conocé el Proyecto (días 1-3)

- [ ] Aceptá la invitación de GitHub: https://github.com/infraitgidas/intellops/invitations
- [ ] Cloná el repo y seguí el [onboarding general](README.md)
- [ ] Leé estos documentos en orden:
  1. `TEAM_CHARTER.md` — conocé al equipo y los valores
  2. `docs/brief-v2.md` — contexto completo del proyecto (prestá atención a las secciones de ML)
  3. `openspec/specs/research/state-of-the-art.md` — estado del arte en AIOps y ML para observabilidad
  4. `openspec/specs/research/hypotheses.md` — línea L1 (tu hipótesis de Fase 1)
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

### Documentos Clave para Fase 1

| Documento | Por qué es importante |
|-----------|----------------------|
| `openspec/specs/research/hypotheses.md` (H1) | Tu hipótesis de Fase 1 con criterios de validación |
| `openspec/specs/research/benchmarking.md` (sección 2.2) | Benchmark de modelos ML que vas a implementar |
| `openspec/specs/research/experiments.md` (EXP-001 a 004) | Tus experimentos de Fase 1 planificados |
| `openspec/specs/architecture/components.md` | Estructura de componentes del ML Engine |
| `openspec/specs/architecture/interfaces.md` | API del ML Engine |
| `openspec/specs/architecture/containers.md` | Footprint y recursos del ML Engine |

### Stack Específico — Fase 1

| Herramienta | Propósito | Estado |
|-------------|-----------|--------|
| Python + scikit-learn | Modelos ML | Listo |
| FastAPI | Backend API | Listo (esqueleto) |
| SQLite | Almacenamiento de métricas | Por implementar |
| DVC | Versionado de datasets | Por configurar |
| MLflow | Tracking de experimentos | Por configurar |
| Evidently | Drift monitoring | Por configurar |
| React + D3.js | Dashboard (3 vistas) | Por implementar |

---

## Fase 2: Agentes IA para UX Predictiva (Sprint 3+)

Una vez que entendés cómo se detectan anomalías en métricas de infra, pasamos al siguiente nivel: **predecir reclamos de usuarios antes de que ocurran** usando agentes de IA sobre trazas OpenTelemetry.

### Tu Rol en Fase 2

| Actividad I+D+i | Por qué es investigación | Qué vas a construir |
|----------------|-------------------------|---------------------|
| **Agente de IA para RCA sobre trazas de usuario** | Aplicar LLMs locales a tracing data para RCA es un área activa de investigación (pocos papers en recursos limitados) | Agente que consume trazas de Tempo + logs de Loki y genera hipótesis de causa raíz |
| **Modelo predictivo de reclamos** | Predecir reclamos de usuarios a partir de métricas de UX no es trivial con ML liviano | Clasificador que predice "este usuario va a tener un problema" usando features OTel |
| **User Health Score** | Sintetizar múltiples señales en un score único y accionable es un problema abierto en AIOps | Algoritmo que combina latencia, errores, throughput en un score 0-100 |
| **Análisis de patrones de incidentes UX** | Identificar correlaciones entre releases, cambios de config y degradación de UX | Dashboard de correlación deploys → UX metrics en Grafana |

### Semana 3-4 — Investigación y Prototipado

- [ ] Leé la especificación H6 en `openspec/specs/research/hypotheses.md`
- [ ] Revisá los experimentos EXP-AI-01 a 04 en `openspec/specs/research/experiments.md`
- [ ] Investigá cómo se estructura un agente de IA para RCA: ¿LangChain, o chain custom con llama.cpp?
- [ ] Armá un PoC de clasificador de reclamos con Random Forest sobre features sintéticos
- [ ] Probá llama.cpp localmente con Llama 3.2 1B para entender capacidades y límites
- [ ] Diseñá el User Health Score: qué métricas incluir, pesos, thresholds

### Semana 5+ — Implementación

```bash
# Primer cambio SDD de Fase 2
# Título: "[change] clasificador-reclamos-otel"
git checkout -b feat/clasificador-reclamos develop

# Implementación:
# - src/ml/predictors/complaint_classifier.py — Clasificador de reclamos
# - src/ml/features/otel_features.py — Feature engineering sobre trazas OTel
# - src/ml/core/user_health_score.py — Algoritmo de User Health Score
# - tests/ml/test_complaint_classifier.py — Tests
```

### Documentos Clave para Fase 2

| Documento | Por qué es importante |
|-----------|----------------------|
| `openspec/specs/research/hypotheses.md` (H6) | Tu hipótesis de Fase 2 |
| `openspec/specs/research/experiments.md` (EXP-AI-*) | Tus experimentos de agentes IA |
| `openspec/specs/architecture/containers.md` | ML Engine + LLM Server actualizados |
| `openspec/specs/architecture/interfaces.md` | Endpoints del agente RCA |

### Stack Específico — Fase 2

| Herramienta | Propósito | Estado |
|-------------|-----------|--------|
| scikit-learn + imbalanced-learn | Clasificador de reclamos | Listo |
| Llama 3.2 1B GGUF + llama.cpp | RCA con LLM local | Investigar |
| sentence-transformers + Chroma | RAG sobre trazas y runbooks | Investigar |
| Tempo (Grafana) | Fuente de trazas para el agente | Por configurar |
| Loki | Fuente de logs para contexto del RCA | Por configurar |
| User Health Score (algoritmo propio) | Score compuesto de salud UX | Por diseñar |

### Referencias Rápidas — Fase 2

- [OpenTelemetry Python](https://opentelemetry.io/docs/languages/python/)
- [llama.cpp](https://github.com/ggerganov/llama.cpp)
- [LangChain](https://www.langchain.com/)
- [Grafana Tempo](https://grafana.com/docs/tempo/latest/)
- [scikit-learn Random Forest](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.RandomForestClassifier.html)

### Checklist de Avance

#### Fase 1
- [ ] Semana 1: Onboarding completo + lectura de docs
- [ ] Semana 2: Esqueleto ML Engine con detector base (primer cambio SDD)
- [ ] Semana 10: Revisión Hito 50%

#### Fase 2
- [ ] Semana 3-4: PoC clasificador de reclamos sobre dataset sintético
- [ ] Semana 5-6: User Health Score diseñado e implementado (primer cambio SDD Fase 2)
- [ ] Semana 8-9: Agente RCA con LLM local + RAG sobre trazas funcionando
- [ ] Semana 14: MVP-1 con clasificador + User Health Score + agente RCA
- [ ] Semana 18: Prototipo funcional completo con dashboards de correlación
- [ ] Semana 20: Informe Final + Paper en conferencia/revista académica

---

*¿Dudas? Abrí un issue con label `setup` o hablá con el coordinador.*
