# Research Hypotheses — IntellOps

- **Versión**: 1.0
- **Fecha**: 2026-05-27
- **Autores**: Emanuel Rodriguez, Equipo InfraIT GIDAS

## Formato de Hipótesis

Cada hipótesis sigue el formato estándar de investigación científica:

- **Hipótesis nula (H₀)**: Lo que se busca refutar
- **Hipótesis alternativa (H₁)**: Lo que se busca demostrar
- **Variables**: Independiente (controlada), dependiente (medida), control (constantes)
- **Criterio de validación**: Métrica cuantitativa target
- **Riesgos**: Factores que podrían invalidar la hipótesis

---

## H1: Detección de Anomalías con ML Liviano

**ID**: H1  
**Línea**: L1 — Observabilidad Predictiva en Recursos Escasos  
**Responsable**: Romeo Monfroglio

### Hipótesis Nula (H₀)
Un modelo Isolation Forest con estadísticos complementarios no supera umbrales de detección aceptables (F1 < 0.70) cuando se ejecuta en hardware con < 2GB RAM y CPU sin GPU.

### Hipótesis Alternativa (H₁)
Un ensamble de Isolation Forest + Z-score dinámico + Seasonal Decomposition alcanza F1 > 0.80 en detección de anomalías operando en < 2GB RAM, CPU-only, con inferencia < 500ms.

### Variables

| Tipo | Variable | Definición | Medición |
|------|----------|------------|----------|
| Independiente | Modelo ML utilizado | Isolation Forest vs Z-score vs ensamble | Configuración del pipeline |
| Dependiente | Precisión de detección | F1-score sobre dataset etiquetado | `sklearn.metrics.f1_score` |
| Dependiente | Latencia de inferencia | Tiempo desde recepción de métrica hasta predicción | `time.perf_counter` |
| Dependiente | Uso de memoria | RAM máxima durante inferencia | `memory_profiler` |
| Control | Dataset de validación | SWaT + Yahoo S5 + GIDAS-Synth | Seeds fijos, splits idénticos |
| Control | Hardware | Servidor GIDAS (4GB RAM, 2 cores CPU) | docker-compose resource limits |

### Criterio de Validación

| Métrica | Target | Mínimo aceptable | Método de medición |
|---------|--------|------------------|-------------------|
| F1 | > 0.85 | > 0.80 | 5-fold cross-validation |
| Precisión | > 0.85 | > 0.80 | TP / (TP + FP) |
| Recall | > 0.80 | > 0.75 | TP / (TP + FN) |
| Latencia | < 100ms | < 500ms | Media de 1000 inferencias |
| RAM | < 50MB | < 100MB | `memory_profiler` en inferencia |

### Experimentos Asociados

- EXP-001: Isolation Forest baseline
- EXP-002: Ensamble Isolation Forest + Z-score
- EXP-003: Ensamble completo con Seasonal Decomposition
- EXP-004: Benchmark de latencia en CPU limitado (2 cores)

### Riesgos de Invalidación

- Dataset sintético no representativo de datos reales del laboratorio
- Overfitting al dataset de validación
- Deriva temporal (concept drift) en producción que degrade el modelo

---

## H2: GenIA Local para RCA

**ID**: H2  
**Línea**: L2 — GenIA Local para Asistencia en Incidentes  
**Responsable**: TBD

### Hipótesis Nula (H₀)
Un LLM cuantizado de 1B parámetros (Llama 3.2 GGUF Q4_K_M) en CPU no genera análisis de causa raíz (RCA) útiles para operadores no expertos (precisión factual < 60%).

### Hipótesis Alternativa (H₁)
Un LLM 1B cuantizado con RAG sobre documentación GIDAS alcanza precisión factual > 80% en RCA de incidentes de infraestructura, con CSAT > 4.0/5.

### Variables

| Tipo | Variable | Definición | Medición |
|------|----------|------------|----------|
| Independiente | Configuración del LLM | RAG vs sin RAG, contexto, temperatura | Template de prompt |
| Dependiente | Precisión factual | % de afirmaciones factualmente correctas | Revisión por experto |
| Dependiente | Satisfacción del usuario | CSAT post-interacción | Cuestionario (n > 10) |
| Dependiente | Velocidad de respuesta | Tokens/segundo | `llama.cpp` benchmark |
| Control | Incidentes de prueba | 20 incidentes simulados con RCA conocido | Mismo set para todos los tests |

### Criterio de Validación

| Métrica | Target | Mínimo aceptable | Método |
|---------|--------|------------------|--------|
| Precisión factual | > 85% | > 80% | Revisión por experto (n=3) |
| CSAT | > 4.5/5 | > 4.0/5 | Cuestionario SUS adaptado |
| Velocidad | > 8 tok/s | > 5 tok/s | llama.cpp benchmark |
| Relevancia | > 4.0/5 | > 3.5/5 | Evaluación por expertos |

### Experimentos Asociados

- EXP-101: RAG baseline sin fine-tuning
- EXP-102: RAG con prompt engineering optimizado
- EXP-103: Comparación Llama 3.2 1B vs TinyLlama 1.1B

---

## H3: Seguridad con Recursos Cero

**ID**: H3  
**Línea**: L3 — Seguridad en Observabilidad Académica  
**Responsable**: Federico Cavallero

### Hipótesis Nula (H₀)
No es posible alcanzar compliance CIS Benchmark Level 1 en infraestructura de laboratorio universitario utilizando exclusivamente herramientas open-source y presupuesto cero.

### Hipótesis Alternativa (H₁)
Es posible alcanzar Lynis compliance score ≥ 70% y detección de eventos simulados en ≤ 60 segundos utilizando Ansible + Grafana/Loki/Prometheus con presupuesto cero.

### Criterio de Validación

| Métrica | Target | Mínimo aceptable | Método |
|---------|--------|------------------|--------|
| Lynis score | > 75% | > 70% | Lynis audit post-hardening |
| Tiempo detección | < 30s | < 60s | Evento simulado → alerta Grafana |
| Dashboards | 4 vistas | 4 vistas | Revisión por PO |
| Costo | $0 | $0 | Tracking de gastos |

### Experimentos Asociados

- EXP-201: Auditoría baseline y hardening CIS Level 1
- EXP-202: Pipeline Grafana + Loki + Prometheus para logs de seguridad
- EXP-203: Dashboards de seguridad (4 vistas)

---

## H4: DevOps en PI+D+i

**ID**: H4  
**Línea**: L4 — DevOps y QA Automatizado en PI+D+i  
**Responsable**: Santiago Montanari

### Hipótesis Nula (H₀)
La adopción de CI/CD con quality gates no mejora significativamente la calidad ni la reproducibilidad en proyectos de investigación con equipos pequeños (< 5 personas).

### Hipótesis Alternativa (H₁)
La implementación de CI/CD con quality gates (coverage ≥ 70%, lint, contract tests) produce mejoras medibles en calidad (defect rate, MTTR) y reproducibilidad (setup time, build reproducibility).

### Criterio de Validación

| Métrica | Target | Mínimo aceptable | Método |
|---------|--------|------------------|--------|
| Coverage | > 80% | > 70% | pytest-cov |
| Pipeline time | < 5 min | < 10 min | GitHub Actions timing |
| Setup time | < 15 min | < 30 min | Cronometrado en máquina limpia |
| MTTR | < 1h | < 4h | Registro de incidentes |

### Experimentos Asociados

- EXP-301: Pipeline CI/CD baseline
- EXP-302: Contract testing con schemathesis
- EXP-303: Benchmark de pipeline time vs coverage trade-off

---

## H5: User Telemetry & Tracing Proactivo

**ID**: H5  
**Línea**: L5 — Observabilidad UX-Céntrica con OpenTelemetry  
**Responsable**: Federico Cavallero  
**Fase**: 2 — Observabilidad Centrada en el Usuario (post-Fase 1)

### Hipótesis Nula (H₀)
Un agente RUM con instrumentación OpenTelemetry en frontend + backend no reduce el tiempo de detección de degradación de experiencia de usuario ni anticipa reclamos en comparación con monitoreo de infraestructura tradicional.

### Hipótesis Alternativa (H₁)
Es posible detectar degradación en experiencia de usuario real (LCP > 2.5s, INP > 200ms, error rate > 1%) con un agente RUM OTel < 30KB y un pipeline Tempo+Loki+Mimir en < 500MB RAM, anticipando reclamos de usuarios con ≥ 85% de precisión y tiempo de detección < 30s.

### Variables

| Tipo | Variable | Definición | Medición |
|------|----------|------------|----------|
| Independiente | Instrumentación OTel aplicada | RUM agent + backend OTel + Collector | Configuración del pipeline |
| Dependiente | Tiempo de detección de degradación UX | Diferencia entre inicio de degradación real y alerta generada | Timestamps correlacionados (Tempo) |
| Dependiente | Bundle size del agente RUM | Tamaño del JS comprimido en producción | `webpack --mode production` |
| Dependiente | Precisión de anticipación de reclamos | % de reclamos anticipados correctamente vs reclamos reales | Correlación alertas vs issues/soportes |
| Control | Aplicación monitoreada | API FastAPI + dashboard React del propio IntellOps | Misma app para todas las mediciones |
| Control | Hardware | Servidor GIDAS (4GB RAM, 2 cores CPU) | docker-compose resource limits |

### Criterio de Validación

| Métrica | Target | Mínimo aceptable | Método de medición |
|---------|--------|------------------|-------------------|
| Tiempo detección degradación UX | < 15s | < 30s | Correlación trazas Tempo + alertas |
| Bundle size agente RUM | < 20KB | < 30KB | gzip comprimido, `webpack --mode production` |
| Precisión anticipación reclamos | > 90% | > 85% | Comparación contra reclamos reales en período de prueba |
| Overhead en rendimiento (LCP) | < 1% | < 3% | Lighthouse con/sin agente |
| RAM pipeline OTel | < 256MB | < 500MB | `docker stats` |

### Experimentos Asociados

- EXP-OTel-01: Implementar agente RUM con OTel JS SDK, medir overhead
- EXP-OTel-02: Pipeline Tempo + Loki + Grafana para trazas de request
- EXP-OTel-03: Sistema de alertas multicanal con routing por criticidad
- EXP-OTel-04: Benchmark de overhead de instrumentación OTel en FastAPI

### Riesgos de Invalidación

- La aplicación demo no genera suficiente tráfico para medir degradación realista
- OpenTelemetry Collector consume más recursos de los estimados en hardware limitado
- Los reclamos de usuario no pueden correlacionarse por cuestiones de privacidad

---

## H6: Agentes IA para UX Predictiva

**ID**: H6  
**Línea**: L6 — AI Agents for Proactive Observability  
**Responsable**: Romeo Monfroglio  
**Fase**: 2 — Observabilidad Centrada en el Usuario (post-Fase 1)

### Hipótesis Nula (H₀)
Un ensemble de modelos livianos sobre features de OpenTelemetry no logra predecir reclamos de usuarios con F1 > 0.70 operando en < 100MB RAM y CPU-only.

### Hipótesis Alternativa (H₁)
Un ensemble de modelos livianos (Random Forest + statistical thresholds + LLM 1B para RCA) sobre features de OpenTelemetry (latencia p99, error rate, throughput, Core Web Vitals) puede predecir reclamos de usuarios con F1 > 0.75, generar RCA en lenguaje natural, y operar en < 100MB RAM + CPU-only para modelos estadísticos, con activación bajo demanda del LLM.

### Variables

| Tipo | Variable | Definición | Medición |
|------|----------|------------|----------|
| Independiente | Configuración del ensemble de modelos | RF vs thresholds vs RF+LLM | Feature set, hiperparámetros |
| Dependiente | Precisión de predicción de reclamos | F1-score sobre reclamos reales etiquetados | Correlación predicciones vs reclamos |
| Dependiente | Calidad del RCA generado | % de análisis de causa raíz factualmente correctos | Revisión por experto (n=3) |
| Dependiente | User Health Score | Score compuesto (0-100) de salud de experiencia de usuario | Algoritmo propio sobre features OTel |
| Control | Dataset de reclamos | Reclamos simulados + históricos de laboratorio GIDAS | Mismo set para todas las corridas |
| Control | Hardware | Servidor GIDAS (4GB RAM, 2 cores CPU) | docker-compose resource limits |

### Criterio de Validación

| Métrica | Target | Mínimo aceptable | Método de medición |
|---------|--------|------------------|-------------------|
| F1 predicción de reclamos | > 0.80 | > 0.75 | 5-fold cross-validation contra reclamos etiquetados |
| Precisión factual RCA | > 85% | > 80% | Revisión por experto (n=3) sobre 20 incidentes |
| User Health Score correlación | r > 0.85 | r > 0.75 | Correlación de Pearson con reclamos reales |
| RAM en inferencia (modelos clásicos) | < 50MB | < 100MB | `memory_profiler` |
| RAM en inferencia (LLM + RAG) | < 600MB | < 800MB | `memory_profiler` (bajo demanda) |

### Experimentos Asociados

- EXP-AI-01: Entrenar clasificador de reclamos sobre dataset sintético de trazas OTel
- EXP-AI-02: Implementar agente de RCA con LLM local + RAG sobre trazas y logs
- EXP-AI-03: Benchmark de User Health Score vs reclamos reales
- EXP-AI-04: Detección de anomalías en trazas OTel (latencia outlier, error burst)

### Riesgos de Invalidación

- Dataset de reclamos sintético no representativo de la complejidad real
- El LLM 1B puede no tener capacidad suficiente para RCA de incidentes complejos
- Concept drift en patrones de uso que degrade la precisión del clasificador

---

## H7: Observability-Driven QA

**ID**: H7  
**Línea**: L7 — Calidad de Software con Señales de Observabilidad  
**Responsable**: Santiago Montanari  
**Fase**: 2 — Observabilidad Centrada en el Usuario (post-Fase 1)

### Hipótesis Nula (H₀)
Un quality gate basado en señales de OpenTelemetry en CI/CD no supera a tests funcionales tradicionales en detección de regresiones de experiencia de usuario.

### Hipótesis Alternativa (H₁)
Un quality gate basado en señales de OpenTelemetry (latencia p99 < 200ms, error rate < 0.1%, trazas completas validadas) en CI/CD detecta regresiones de UX con > 80% precisión, superando a tests funcionales tradicionales (precisión < 60%) en detección de problemas de performance, con un overhead de pipeline < 3 minutos.

### Variables

| Tipo | Variable | Definición | Medición |
|------|----------|------------|----------|
| Independiente | Tipo de quality gate | OTel-based vs tests funcionales vs ambos | Configuración del pipeline CI |
| Dependiente | Precisión de detección de regresiones UX | % de regresiones detectadas correctamente | Validación contra releases con regresiones conocidas |
| Dependiente | Overhead de pipeline | Tiempo adicional en CI por los quality gates OTel | GitHub Actions timing |
| Dependiente | Falso positivos | % de alertas incorrectas de degradación UX | Revisión manual de cada alerta |
| Control | Aplicación bajo prueba | IntellOps API + dashboard en entorno de staging | Misma app para todos los gates |
| Control | Tráfico sintético | Locust con journeys de usuario OTel-instrumentados | Mismos scripts para todas las corridas |

### Criterio de Validación

| Métrica | Target | Mínimo aceptable | Método de medición |
|---------|--------|------------------|-------------------|
| Precisión detección regresiones UX | > 85% | > 80% | Validación contra 10 regresiones conocidas |
| Overhead de pipeline | < 2 min | < 3 min | GitHub Actions timing con/sin gates OTel |
| Falsos positivos | < 10% | < 15% | Revisión manual de alertas del quality gate |
| Cobertura de trazas validadas | > 90% | > 80% | % de endpoints cubiertos por synthetic journeys OTel |

### Experimentos Asociados

- EXP-QA-01: Synthetic user journeys con OTel propagation y validación en Tempo
- EXP-QA-02: Quality gates basados en métricas OTel en CI/CD
- EXP-QA-03: Chaos engineering controlado midiendo User Health Score
- EXP-QA-04: CBA de observabilidad: incidentes evitados, MTTR, costo

### Riesgos de Invalidación

- Synthetic journeys no representan la variabilidad del tráfico real de usuarios
- El entorno de CI puede no tener recursos suficientes para correr OTel Collector + Tempo
- Regresiones de UX detectadas pueden no ser accionables para el equipo de desarrollo
