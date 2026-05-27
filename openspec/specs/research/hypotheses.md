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
