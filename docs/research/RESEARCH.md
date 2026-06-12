# Research Log — IntellOps

Este documento registra las líneas de investigación activas, hipótesis, experimentos y publicaciones del proyecto.

## Líneas de Investigación

### L1: Observabilidad Predictiva en Recursos Escasos

- **Hipótesis**: Es posible detectar anomalías en infraestructura IT con modelos ML ligeros (Isolation Forest + estadísticos) operando en hardware con < 2GB RAM y CPU sin GPU.
- **Método**: Evaluación comparativa de Isolation Forest, Z-score dinámico, seasonal decomposition en datasets sintéticos y reales.
- **Métrica target**: F1 > 0.80, MAPE < 15%, inferencia < 500ms en CPU.
- **Responsable**: Romeo Monfroglio

### L2: GenIA Local para Asistencia en Investigación de Incidentes

- **Hipótesis**: Un LLM cuantizado de 1B parámetros (Llama 3.2 GGUF 4-bit) corriendo en CPU puede generar RCA (Root Cause Analysis) útiles para operadores no expertos.
- **Método**: RAG sobre documentación GIDAS + runbooks históricos, evaluación con operadores reales.
- **Métrica target**: CSAT > 4.0/5, precisión factual > 80%.
- **Responsable**: TBD

### L3: Seguridad en Sistemas de Observabilidad Académicos

- **Hipótesis**: Es posible alcanzar compliance CIS Benchmark Level 1 en infraestructura de laboratorio universitario con herramientas open-source y presupuesto cero.
- **Método**: Auditoría con Lynis/OpenSCAP, hardening con Ansible, monitoreo con Grafana + Loki + Prometheus.
- **Métrica target**: Lynis score >= 70%, detección de evento simulado <= 60s.
- **Responsable**: Federico Cavallero

### L4: DevOps y QA Automatizado en PI+D+i

- **Hipótesis**: La adopción de CI/CD con quality gates y contract testing mejora la calidad y reproducibilidad en proyectos de investigación de recursos escasos.
- **Método**: Implementación de pipeline GitLab CI/CD con tests automatizados, medición de cobertura y tiempo de pipeline.
- **Métrica target**: Coverage >= 70%, pipeline <= 10 min/commit.
- **Responsable**: Santiago Montanari

### L5: Observabilidad UX-Céntrica con OpenTelemetry (Frontend)

- **Hipótesis**: Es posible detectar degradación en experiencia de usuario real (LCP > 2.5s, INP > 200ms, error rate > 1%) con un agente RUM OTel < 30KB y un pipeline Tempo+Loki+Mimir en < 500MB RAM, anticipando reclamos de usuarios con ≥ 85% de precisión.
- **Método**: Instrumentación OTel en frontend + backend, pipeline LGTM, agentes IA para RCA predictiva.
- **Métrica target**: Bundle < 30KB, detección < 30s, precisión anticipación > 85%.
- **Estado del arte**: `docs/research/frontend-observability.md`
- **Responsable**: Federico Cavallero (Fase 2)

## Experimentos Activos

| ID | Línea | Experimento | Estado | Fecha | MLflow |
|----|-------|-------------|--------|-------|--------|
| — | — | — | — | — | — |

*Registrar cada experimento en `ml/experiments/` con MLflow.*

## Publicaciones Planificadas

| Título Tentativo | Venues Primarios | Autores | Estado | Línea |
|------------------|-----------------|---------|--------|-------|
| IntellOps: Observabilidad Predictiva UX-Céntrica en Recursos Escasos | SREcon, CLEI, JSS | Monfroglio, Cavallero, Montanari, Rodriguez, Nahuel | En desarrollo | L1 |
| Agente RUM Liviano con OTel para Monitoreo de Experiencia de Usuario | SREcon, ObservabilityCON, SPE | Cavallero, Rodriguez, Nahuel | Planificado | L5 |
| Predicción de Reclamos de Usuario mediante ML sobre Señales de UX | ISSRE, EMSE, CLEI | Monfroglio, Rodriguez, Nahuel | Planificado | L1 / H6 |
| Quality Gates basados en OpenTelemetry para CI/CD en I+D+i | FSE, ASE, JSS | Montanari, Rodriguez, Nahuel | Planificado | L4 / H7 |
| Seguridad en Observabilidad Académica con Stack GLP | CACIC, IEEE LATAM, JAIIO | Cavallero, Rodriguez, Nahuel | Planificado | L3 |
| DevOps y QA Automatizado en PI+D+i: Estudio Empírico | EMSE, IST, JAIIO | Montanari, Rodriguez, Nahuel | Planificado | L4 |

📄 **Ver catálogo completo de venues**: [`docs/research/publication-venues.md`](publication-venues.md)

## Datasets

| Dataset | Descripción | Registro | DOI |
|---------|-------------|----------|-----|
| — | — | — | — |

*Los datasets se versionan con DVC y se publican en Zenodo/OSF con DOI.*

## Venues de Publicación

Ver el catálogo completo en [`docs/research/publication-venues.md`](publication-venues.md) con:
- **Conferencias académicas**: JAIIO, CACIC, CLEI, ISSRE, SREcon, FSE, ASE, ICSE, LACCEL, SLCARS, WICC, SBSI, ICPC
- **Revistas con referato**: IEEE TSE, ACM CSUR, JSS, EMSE, SPE, IEEE Software, IEEE Access, IST, IEEE LATAM, JWE, RASI
- **Eventos de industria**: SREcon, ObservabilityCON, KubeCon, Monitorama, DevOpsDays, PlatformCon

## Hipótesis Abiertas

- ¿Puede un LLM 1B mantener precisión factual > 80% en RCA sin fine-tuning?
- ¿SQLite con índices temporales es suficiente para 1K métricas/seg en períodos de 6 meses?
- ¿El overhead de CI/CD se justifica en proyectos de investigación con equipos de 3 personas?
