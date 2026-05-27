# Research Specification — IntellOps

- **Domain**: Investigación Científica
- **Estado**: Activo
- **Última actualización**: 2026-05-27
- **Autores**: Emanuel Rodriguez, Equipo InfraIT GIDAS

## Propósito

Esta especificación define el marco de investigación científica del proyecto IntellOps. Establece las líneas de investigación, metodologías, criterios de validación y el plan de publicaciones del PI+D+i.

## Líneas de Investigación

| ID | Línea | Hipótesis Central | Método | Responsable |
|----|-------|-------------------|--------|-------------|
| L1 | Observabilidad Predictiva en Recursos Escasos | ML liviano (Isolation Forest + estadísticos) en < 2GB RAM puede detectar anomalías con F1 > 0.80 | Benchmark comparativo, datasets sintéticos + reales | Romeo Monfroglio |
| L2 | GenIA Local para Asistencia en Incidentes | LLM 1B cuantizado en CPU puede generar RCA útil para operadores no expertos | RAG + evaluación con usuarios, CSAT | TBD |
| L3 | Seguridad en Observabilidad Académica | Compliance CIS Level 1 alcanzable con herramientas open-source y presupuesto cero | Auditoría + hardening + monitoreo GLP | Federico Cavallero |
| L4 | DevOps y QA Automatizado en PI+D+i | CI/CD con quality gates mejora calidad y reproducibilidad en investigación | Implementación + medición de métricas DORA | Santiago Montanari |

## Documentos de Investigación

| Documento | Propósito | Formato |
|-----------|-----------|---------|
| `state-of-the-art.md` | Estado del arte formal con referencias académicas y de industria | Spec |
| `benchmarking.md` | Metodología y resultados de benchmarking de productos y modelos | Spec |
| `market-analysis.md` | Análisis de mercado, posicionamiento y nicho | Spec |
| `hypotheses.md` | Hipótesis de investigación formales con criterios de validación | Spec |
| `experiments.md` | Metodología experimental y registro de experimentos | Spec |
| `../../docs/research/RESEARCH.md` | Research log vivo con estado de experimentos y papers | Living doc |

## Metodología de Investigación

El proyecto sigue una metodología de **Investigación-Acción en Ingeniería de Software (Action Research)** combinada con **Design Science Research (DSR)**:

1. **Identificación del problema**: Análisis de brecha entre soluciones existentes y necesidades del contexto de recursos escasos.
2. **Diseño del artefacto**: Desarrollo iterativo del sistema IntellOps siguiendo SDD.
3. **Validación**: Experimentos controlados, estudios de caso, evaluación con usuarios reales.
4. **Reflexión**: Análisis de resultados, refinamiento de hipótesis, documentación de lecciones aprendidas.
5. **Publicación**: Difusión de resultados en venues académicos y de industria.

## Criterios de Validación Científica

| Criterio | Estándar | Aplicación en IntellOps |
|----------|----------|------------------------|
| **Reproducibilidad** | Experimentos con seed fijo, pipelines versionadas | DVC + MLflow, `make reproduce` |
| **Validez interna** | Control de variables, grupos de control | Benchmarks contra baseline (sin ML) |
| **Validez externa** | Generalización a otros contextos | Evaluación en 2+ laboratorios piloto |
| **Confiabilidad** | Resultados consistentes en múltiples ejecuciones | Múltiples seeds, análisis estadístico |
| **Objetividad** | Mediciones cuantitativas, revisión por pares | Métricas pre-definidas, code review |

## Estándares de Publicación

- Formato de papers: IEEE/ACM (plantilla LaTeX)
- Repositorio de datos: Zenodo/OSF con DOI
- Código: GitHub con releases semánticos
- Licencia de publicación: CC-BY 4.0 para papers, Apache-2.0 para código

## Referencias

- Hevner, A. R. et al. (2004). Design Science in Information Systems Research. *MIS Quarterly*, 28(1), 75-105.
- Wohlin, C. et al. (2012). *Experimentation in Software Engineering*. Springer.
- ISO/IEC 25010:2011 — Systems and software Quality Requirements and Evaluation (SQuaRE)
- FAIR Principles — Wilkinson, M. et al. (2016). The FAIR Guiding Principles for scientific data management and stewardship. *Scientific Data*, 3.
