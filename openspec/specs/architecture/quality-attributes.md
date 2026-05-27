# Quality Attributes Specification — IntellOps

- **Versión**: 1.0
- **Fecha**: 2026-05-27
- **Autores**: Emanuel Rodriguez, Equipo InfraIT GIDAS

## 1. Marco de Referencia

Los atributos de calidad se definen siguiendo **ISO/IEC 25010:2011** (SQuaRE — Systems and software Quality Requirements and Evaluation).

Cada atributo se especifica como un **escenario de calidad** siguiendo el formato:

> **Fuente** → **Estímulo** → **Artefacto** → **Entorno** → **Respuesta** → **Medición**

## 2. Atributos de Calidad del Software

### 2.1. Disponibilidad (Availability)

| Elemento | Especificación |
|----------|---------------|
| **Fuente** | Usuarios internos (SREs, admins) |
| **Estímulo** | Solicitud de consulta de métricas/dashboard |
| **Artefacto** | Sistema IntellOps completo |
| **Entorno** | Operación normal en servidor GIDAS |
| **Respuesta** | El sistema responde dentro del tiempo esperado |
| **Medición** | **Target**: 99.5% uptime | **Mínimo**: 99% |
| **Estrategia** | Docker Compose con restart: always, health checks, Netdata auto-monitoreo |

### 2.2. Rendimiento (Performance)

| Elemento | Especificación |
|----------|---------------|
| **Fuente** | Agente RUM / API externa |
| **Estímulo** | Envío de 1000 métricas/seg en burst |
| **Artefacto** | Endpoint `/metrics/ingest` |
| **Entorno** | Carga normal en servidor GIDAS |
| **Respuesta** | Acepta métricas, responde 202, persiste en < 500ms |
| **Medición** | **Target**: < 200ms p99 | **Mínimo**: < 500ms p99 |
| **Estrategia** | FastAPI async, SQLite WAL mode, batching configurable |

| Elemento | Especificación |
|----------|---------------|
| **Fuente** | Dashboard React |
| **Estímulo** | Carga de vista de latencias |
| **Artefacto** | API `/dashboard/summary` |
| **Entorno** | 10K+ métricas almacenadas |
| **Respuesta** | Responde con datos agregados |
| **Medición** | **Target**: < 1s | **Mínimo**: < 2s |
| **Estrategia** | Agregación en SQL, índices temporales, paginación |

### 2.3. Usabilidad (Usability)

| Elemento | Especificación |
|----------|---------------|
| **Fuente** | SRE Estudiante (no experto en ML) |
| **Estímulo** | Primera interacción con el dashboard |
| **Artefacto** | Dashboard IntellOps |
| **Entorno** | Laboratorio GIDAS, sin capacitación previa |
| **Respuesta** | Completa tarea de identificar anomalía en < 10 segundos |
| **Medición** | **Target**: SUS > 80 | **Mínimo**: SUS > 75 |
| **Estrategia** | Progressive disclosure, texto explicativo, tooltips contextuales |

### 2.4. Mantenibilidad (Maintainability)

| Elemento | Especificación |
|----------|---------------|
| **Fuente** | Desarrollador del equipo |
| **Estímulo** | Modificar un detector de anomalías existente |
| **Artefacto** | Código fuente del ML Engine |
| **Entorno** | Desarrollo, con specs y ADRs disponibles |
| **Respuesta** | Cambio implementado, tests pasan, coverage se mantiene |
| **Medición** | **Target**: Coverage > 80% | **Mínimo**: > 70% |
| **Estrategia** | TDD, CI/CD con quality gates, linters, ADRs |

### 2.5. Portabilidad (Portability)

| Elemento | Especificación |
|----------|---------------|
| **Fuente** | Investigador en otra universidad |
| **Estímulo** | Ejecutar `docker compose up` en máquina limpia |
| **Artefacto** | Repositorio completo de IntellOps |
| **Entorno** | Hardware genérico (x86_64 o arm64, 4GB RAM, sin GPU) |
| **Respuesta** | Sistema operativo y funcional en < 30 minutos |
| **Medición** | **Target**: < 15 min | **Mínimo**: < 30 min |
| **Estrategia** | Docker Compose, make setup, onboarding documentado |

### 2.6. Seguridad (Security)

| Elemento | Especificación |
|----------|---------------|
| **Fuente** | Usuario no autenticado / atacante externo |
| **Estímulo** | Acceso a endpoints de administración |
| **Artefacto** | FastAPI Backend |
| **Entorno** | Red del laboratorio GIDAS |
| **Respuesta** | Rechaza acceso, registra intento |
| **Medición** | **Target**: OWASP Top 10 sin críticos | **Mínimo**: Sin críticos |
| **Estrategia** | API key validation, CORS restrictivo, rate limiting, CIS hardening |

### 2.7. Eficiencia de Recursos (Resource Efficiency)

| Elemento | Especificación |
|----------|---------------|
| **Fuente** | Sistema completo en operación |
| **Estímulo** | Operación normal (ingesta + consulta + ML) |
| **Artefacto** | Todos los contenedores |
| **Entorno** | Servidor GIDAS (4GB RAM, 2 cores) |
| **Respuesta** | Consumo dentro de límites |
| **Medición** | **Target**: < 2GB RAM | **Mínimo**: < 3GB RAM |
| **Estrategia** | Contenedores con resource limits, modelos cuantizados, SQLite |

### 2.8. Reproducibilidad (Reproducibility) — Atributo Específico PI+D+i

| Elemento | Especificación |
|----------|---------------|
| **Fuente** | Investigador externo |
| **Estímulo** | Clonar repo y ejecutar experimento |
| **Artefacto** | Repositorio + DVC + MLflow |
| **Entorno** | Cualquier máquina con Docker |
| **Respuesta** | Experimentos reproducen métricas publicadas |
| **Medición** | **Target**: 100% experimentos reproducibles | **Mínimo**: > 80% |
| **Estrategia** | Seeds fijos, DVC pipelines, MLflow tracking, specs versionadas |

## 3. Escenarios de Atributos de Calidad (Resumen)

| ID | Atributo | Escenario | Target | Prioridad |
|----|----------|-----------|--------|-----------|
| QA-01 | Disponibilidad | Sistema operativo 24/7 | 99.5% uptime | Alta |
| QA-02 | Performance | Ingesta 1K métricas/seg | < 200ms p99 | Alta |
| QA-03 | Performance | Dashboard carga | < 1s | Alta |
| QA-04 | Performance | Detección anomalía | < 5s | Alta |
| QA-05 | Performance | GenIA inferencia | 5-10 tok/s | Media |
| QA-06 | Usabilidad | SUS score | > 80 | Alta |
| QA-07 | Usabilidad | Time-to-Anomaly | < 10s | Alta |
| QA-08 | Mantenibilidad | Coverage | > 80% | Alta |
| QA-09 | Portabilidad | Setup time | < 30 min | Alta |
| QA-10 | Seguridad | OWASP Top 10 | Sin críticos | Alta |
| QA-11 | Recursos | Footprint RAM | < 2GB | Alta |
| QA-12 | Recursos | Costo operativo | $0/mes | Alta |
| QA-13 | Reproducibilidad | Experimentos | 100% | Alta |

## 4. Trade-offs entre Atributos

| Trade-off | Decisión | Impacto |
|-----------|----------|---------|
| Performance vs Recursos | Batching en ingesta para reducir CPU | Aumenta latencia de p99 pero reduce consumo |
| Usabilidad vs Portabilidad | Dashboard React static (sin SSR) | Menor performance percepción en primera carga |
| Seguridad vs Usabilidad | API key en cada request | Menos conveniente para desarrollo, necesario para producción |
| Reproducibilidad vs Velocidad | Seed fijo en experimentos | Resultados consistentes pero menor flexibilidad exploratoria |
| Mantenibilidad vs Recursos | Monolito modular (no microservicios) | Menor escalabilidad pero mucho más mantenible |
