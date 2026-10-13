# Architecture Specification — IntellOps

- **Domain**: Arquitectura y Diseño de Sistemas
- **Estado**: Activo
- **Última actualización**: 2026-10-13
- **Autores**: Emanuel Rodriguez, Equipo InfraIT GIDAS

## 1. Visión General

IntellOps es un sistema de **observabilidad predictiva** diseñado bajo el paradigma de **monolito modular**, optimizado para recursos escasos (< 2GB RAM, CPU-only) y con una arquitectura **API-first, contract-driven**.

### 1.1. Principios Arquitectónicos

| Principio | Descripción | Implicancia |
|-----------|-------------|-------------|
| **Monolito Modular** | Código organizado en módulos con boundaries claros, deployado como una sola unidad | Menor complejidad operativa, sin latencia de red entre módulos, fácil de entender |
| **API-First** | Las APIs se diseñan antes que la implementación, con contratos versionados | Permite desarrollo paralelo, testing temprano, y documentación automática |
| **Contract-Driven** | OpenAPI 3.1 + AsyncAPI 3.0 como fuente de verdad para integraciones | Validación automática en CI, evita breaking changes no detectados |
| **Recursos Escasos First** | Cada decisión técnica prioriza el mínimo consumo de recursos | SQLite > TimescaleDB, Llama 1B > 8B, React static > SSR |
| **Evolucionabilidad** | Diseño que permite migrar a stacks más potentes sin reescribir | SQLite migrable a TimescaleDB, Static React migrable a SSR |
| **Observable por Diseño** | El sistema se auto-monitorea con Netdata | Métricas de salud del propio IntellOps |

### 1.2. Diagrama C4 — Contexto (Nivel 1)

```mermaid
C4Context
    Person(sre, "SRE Estudiante", "Administra servicios, necesita detectar anomalías")
    Person(investigador, "Docente/Investigador", "Publica papers, necesita reproducibilidad")
    Person(admin, "Admin Infraestructura", "Gestiona 20+ servicios")
    Person(visitante, "Visitante/Extensión", "Ve demo del laboratorio")

    System_Boundary(intellops, "IntellOps") {
        System(intellops_system, "IntellOps Platform", "Observabilidad predictiva con ML y GenIA")
    }

    System_Ext(monitored, "Infraestructura Monitoreada", "Servidores GIDAS, servicios, apps")
    System_Ext(webhook, "Sistemas de Notificación", "Discord, Slack, Email")
    System_Ext(cloud, "Free-Tier Cloud", "Backup S3, recursos complementarios")

    Rel(sre, intellops_system, "Monitorea, consulta anomalías")
    Rel(investigador, intellops_system, "Exporta datos, reproduce experimentos")
    Rel(admin, intellops_system, "Configura, recibe alertas")
    Rel(visitante, intellops_system, "Visualiza dashboard público")
    Rel(intellops_system, monitored, "Recolecta métricas y logs")
    Rel(intellops_system, webhook, "Envía alertas")
    Rel(intellops_system, cloud, "Backup y burst")
```

### 1.3. Stakeholders

| Stakeholder | Interés | Preocupación Arquitectónica |
|-------------|---------|---------------------------|
| SRE Estudiante | Detectar anomalías rápido | Usabilidad, latencia de detección |
| Docente/Investigador | Reproducibilidad, datos exportables | Portabilidad, trazabilidad |
| Admin Infraestructura | Visibilidad unificada, alertas efectivas | Confiabilidad, mantenibilidad |
| Visitante/Extensión | Demo funcional, sin acceso interno | Seguridad, aislamiento |
| Coordinador | Progreso del proyecto, métricas | Mantenibilidad, extensibilidad |
| Director GIDAS | Publicaciones, transferencia | Reproducibilidad, apertura |

## 2. Decisiones Arquitectónicas Clave

| Decisión | Opción Elegida | Alternativa Descartada | Fundamento |
|----------|---------------|----------------------|------------|
| Estilo arquitectónico | Monolito modular | Microservicios | < 2GB RAM, equipo pequeño, sin necesidad de escalado independiente |
| Base de datos | SQLite con time-index | TimescaleDB, MongoDB | Zero config, zero RAM adicional, migrable |
| Framework backend | FastAPI | Django, Flask, Go | Async nativo, auto-docs OpenAPI, familiaridad del equipo |
| LLM | Llama 3.2 1B GGUF 4-bit | GPT-4 API, Llama 8B | Costo $0, privacidad, funciona en CPU |
| Dashboard | React static build | Next.js, Angular | Sin SSR, < 1MB bundle, hosting estático |
| Logs | Grafana + Loki | ELK Stack | Ver ADR-0001 |
| CI/CD | GitHub Actions | GitLab CI, Jenkins | Free para repos públicos, integración nativa |
| Contenedores | Docker Compose | Kubernetes | Single-node, setup < 30 min |

## 3. Documentos de Arquitectura

| Documento | Propósito | Formato |
|-----------|-----------|---------|
| `spec.md` | Esta especificación — overview, principios, C4 context | Spec |
| `containers.md` | Diagrama C4 de contenedores + decisiones tecnológicas | Spec |
| `components.md` | Diseño de componentes internos | Spec |
| `quality-attributes.md` | Escenarios de atributos de calidad (ISO 25010) | Spec |
| `constraints.md` | Restricciones arquitectónicas y principios de diseño | Spec |
| `interfaces.md` | Índice de contratos de API | Spec |
| `../../docs/adr/*.md` | Architecture Decision Records | ADR |

## Requirements

### Requirement: ARCH-5 (orden del pipeline de ingesta)

El pipeline de ingesta DEBE documentarse e implementarse como `Raw → Normalize → Validate → Enqueue → Store`: una etapa de normalización en el dominio DEBE correr antes de la validación por evento, y la validación DEBE seguir siendo la autoridad única de rechazo. La normalización DEBE resolver representaciones (timestamp, unidad, nombre) que de otro modo la validación rechazaría.
(Previamente: sin etapa de normalización con nombre; la única coerción era implícita en el worker de infraestructura, post-`202`.)

#### Scenario: Orden observable

- GIVEN el flujo de ingesta
- WHEN se envía un evento que lleva un alias de unidad
- THEN la normalización corre primero y la validación ve el evento canónico

#### Scenario: Autoridad de rechazo sin cambios

- GIVEN un evento canónico que viola una cota de sanity
- WHEN corre la validación
- THEN la validación (no la normalización) devuelve la razón de rechazo

### Requirement: ARCH-6 (flexibilidad de contrato documentada)

La declaración `RumMetric.unit` de OpenAPI DEBE ampliarse para aceptar la familia de alias (`s`, `sec`, `secs`, `msec`, `millis`, `counts`) junto con `ms`/`count`, para que el contrato documentado coincida con la flexibilidad en runtime. La ampliación DEBE ser retrocompatible; las unidades y nombres de métrica desconocidos DEBEN seguir rechazándose.

#### Scenario: El contrato refleja los alias

- GIVEN el `openspec/specs/openapi.yaml` actualizado
- WHEN se inspecciona `RumMetric.unit`
- THEN la familia de alias se acepta y la semántica de envelope / `schema_version` no cambia
