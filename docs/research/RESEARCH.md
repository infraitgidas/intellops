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
- **Método**: Auditoría con Lynis/OpenSCAP, hardening con Ansible, monitoreo con ELK Stack.
- **Métrica target**: Lynis score >= 70%, detección de evento simulado <= 60s.
- **Responsable**: Federico Cavallero

### L4: DevOps y QA Automatizado en PI+D+i

- **Hipótesis**: La adopción de CI/CD con quality gates y contract testing mejora la calidad y reproducibilidad en proyectos de investigación de recursos escasos.
- **Método**: Implementación de pipeline GitLab CI/CD con tests automatizados, medición de cobertura y tiempo de pipeline.
- **Métrica target**: Coverage >= 70%, pipeline <= 10 min/commit.
- **Responsable**: Santiago Montanari

## Experimentos Activos

| ID | Línea | Experimento | Estado | Fecha | MLflow |
|----|-------|-------------|--------|-------|--------|
| — | — | — | — | — | — |

*Registrar cada experimento en `ml/experiments/` con MLflow.*

## Publicaciones Planificadas

| Título Tentativo | Venue Target | Autores | Estado | Línea |
|------------------|--------------|---------|--------|-------|
| Observabilidad Predictiva en Recursos Escasos: IntellOps GIDAS | JAIIO 2026 / CACIC 2026 | Monfroglio, Rodriguez, Nahuel | En desarrollo | L1 |
| Seguridad en Observabilidad Académica: Hardening CIS + ELK en IntellOps | CACIC 2026 / JAIIO 2026 | Cavallero, Rodriguez, Nahuel | Planificado | L3 |
| Adopción de DevOps y QA Automatizado en PI+D+i | JAIIO 2026 | Montanari, Rodriguez, Nahuel | Planificado | L4 |

## Datasets

| Dataset | Descripción | Registro | DOI |
|---------|-------------|----------|-----|
| — | — | — | — |

*Los datasets se versionan con DVC y se publican en Zenodo/OSF con DOI.*

## Hipótesis Abiertas

- ¿Puede un LLM 1B mantener precisión factual > 80% en RCA sin fine-tuning?
- ¿SQLite con índices temporales es suficiente para 1K métricas/seg en períodos de 6 meses?
- ¿El overhead de CI/CD se justifica en proyectos de investigación con equipos de 3 personas?
