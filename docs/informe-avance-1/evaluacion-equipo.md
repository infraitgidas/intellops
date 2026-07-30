# Evaluación del Equipo — Informe de Avance 1

> **Roles aplicados**: Project Lead · Scrum Master · Product Owner  
> **Proyecto**: IntellOps — Observabilidad Predictiva con ML y GenIA  
> **Grupo**: InfraIT · GIDAS · UTN FRLP  
> **Fecha**: 30 de julio de 2026

---

## Índice

1. [Análisis del Caso de Negocio](#1-análisis-del-caso-de-negocio)
2. [Análisis del Camino de Diseño](#2-análisis-del-camino-de-diseño)
3. [Evaluación desde Project Lead](#3-evaluación-desde-project-lead)
4. [Evaluación desde Scrum Master](#4-evaluación-desde-scrum-master)
5. [Evaluación desde Product Owner](#5-evaluación-desde-product-owner)
6. [Evaluación Individual: Federico (BlancoCavallero)](#6-evaluación-individual-federico)
7. [Evaluación Individual: Romeo (RomeKai)](#7-evaluación-individual-romeo)
8. [Evaluación Individual: Santiago (Monta702)](#8-evaluación-individual-santiago)
9. [Sugerencias de Arquitectura de Software](#9-sugerencias-de-arquitectura-de-software)
10. [Sugerencias Tecnológicas](#10-sugerencias-tecnológicas)
11. [Sugerencias de Management](#11-sugerencias-de-management)
12. [Próximos Pasos para el Desarrollo](#12-próximos-pasos-para-el-desarrollo)

---

## 1. Análisis del Caso de Negocio

### 1.1. Lo que está bien

El caso de negocio (Federico + brief-v2 de Emanuel) tiene **argumentos sólidos**:

- **Identificación clara del nicho**: El cuadrante "Bajo Recurso + Alta AI" es genuinamente inexplorado. Las soluciones comerciales (Datadog, Dynatrace) son prohibitivas para universidades públicas. Las OSS (Prometheus + Grafana) requieren integración manual que un laboratorio sin equipo de MLOps no puede sostener.

- **Análisis competitivo realista**: Reconoce correctamente que Datadog/Dynatrace no son competidores directos — son aviones versus una bicicleta. El target es otro.

- **Propuesta de valor honesta**: No promete magia. Dice: "aislamiento forest + LSTM controlado + GenIA local". Eso es alcanzable.

- **Restricción de recursos como feature, no como bug**: El "costo $0/mes" y "setup < 30 min" son argumentos de venta legítimos para el ámbito académico.

### 1.2. Lo que preocupa

- **El caso de negocio está desacoplado de las HU**: El caso de negocio habla de un agente Python con Isolation Forest + LSTM. Las HU hablan de 5 métricas RUM (TTFB, FCP, etc.) desde el navegador. **Son dos productos diferentes**. El caso de negocio describe un agente de infraestructura (servidores), mientras que las HU describen un sistema de RUM (navegadores). No hay un documento que unifique ambas visiones.

- **La brecha "investigación ↔ desarrollo"**: Hay investigación excelente (Emanuel, Romeo) y hay HU bien escritas (Federico), pero **no hay trazabilidad** entre una cosa y la otra. ¿Qué HU implementa qué hallazgo de investigación? No está documentado.

- **Las HU asumen un backend más complejo del planificado**: HU-07 habla de Loki para logs, HU-08 de trazas distribuidas. El plan dice SQLite + polling. Hay un gap entre la ambición de las HU y la restricción de recursos del caso de negocio.

### 1.3. Veredicto del Caso de Negocio

> **Sólido en diagnóstico, lábil en ejecución**. El "qué" y el "por qué" están claros. El "cómo" concreto (trazabilidad entre investigación, HU y código) no está resuelto.

---

## 2. Análisis del Camino de Diseño

### 2.1. Lo que está bien

- **SDD como metodología**: Elegir Spec-Driven Development para un proyecto I+D+i es una decisión acertada. Las specs son el artefacto que permite que 4 personas trabajen de forma asíncrona.

- **Stack tecnológico coherente**: FastAPI + SQLite + Grafana LGTM + scikit-learn + Llama.cpp es una combinación sensata para recursos escasos. Cada tecnología está justificada con su alternativa descartada.

- **DER V1 → V1.2 muestra evolución**: La capacidad de iterar el modelo de datos (agregando multi-tenant, JSONB, MLOps) es señal de que hay pensamiento arquitectónico.

- **Plan de trabajo granular**: Las tareas en `plan-trabajo.md` tienen criterios de aceptación, dependencias, esfuerzo y ramas ejemplo. Eso es madurez de gestión de proyectos.

### 2.2. Lo que preocupa

- **El camino de diseño es inconsistentemente documentado**: Emanuel tiene todo en Markdown (versionable, reviewable). Federico, Romeo y Santiago tienen todo en PDF (inrevisable, indifeable). Esto crea dos categorías de contributors: los que se pueden review y los que no.

- **No hay OpenAPI spec escrita todavía**: A pesar de que el brief-v2 y el plan-trabajo mencionan OpenAPI 3.1 + AsyncAPI 3.0 como estándar, **no existe** una spec de API en el repo. El contrato no existe.

- **El DER no está conectado con el stack real**: El DER define tablas como `ML_MODEL`, `ANOMALY`, `ALERT`. Pero el plan de implementación dice SQLite para el MVP. SQLite no soporta nativamente el modelo relacional completo con joins pesados que las consultas ML van a necesitar. ¿Cómo se resuelve esto? No está documentado.

- **No hay trazabilidad HU → DER → Código**: Las HU mencionan "5 métricas deterministas" (TTFB, FCP, XHR, JS Errors, Rage Clicks). El DER tiene `RUM_METRIC` con `metric_type` como string. ¿Cómo se asegura que el `metric_type='TTFB'` en la DB corresponde a la HU-09? No hay un mapa de trazabilidad.

### 2.3. Veredicto del Camino de Diseño

> **Buenos bloques de construcción individuales, pero sin pegamento entre ellos**. Es como tener los planos de la cocina, el baño y el living por separado, pero sin el plano de la casa. El próximo paso debería ser un **mapa de trazabilidad** que conecte: Hipótesis → Experimentos → HU → DER → API Spec → Código.

---

## 3. Evaluación desde Project Lead

### 3.1. Fortalezas del Equipo

| Aspecto | Evaluación |
|---------|-----------|
| **Visión compartida** | El equipo tiene claro el "para qué". Todos los documentos apuntan en la misma dirección |
| **Investigación** | Nivel de profundidad académica alto. Los 3 documentos de Emanuel son publicables como survey |
| **Plan de trabajo** | Excepcionalmente detallado. Tareas con criterios de aceptación, dependencias, ramas |
| **Stack definido** | No hay discusiones eternas sobre tecnología. Está decidido y justificado |

### 3.2. Debilidades del Equipo

| Aspecto | Evaluación |
|---------|-----------|
| **Distribución de carga** | Emanuel concentra ~51% del esfuerzo estimado. Si él se ausenta, el proyecto se detiene |
| **Sin reviews** | 0 reviews en el PR #7. La dinámica de revisión por pares no existe |
| **PDFs como entregables** | 14 PDFs que no se pueden diff, review ni versionar adecuadamente |
| **Sin código funcionando** | El proyecto tiene un esqueleto FastAPI + tests, pero no hay lógica de negocio implementada |
| **Dependencia del coordinador** | Todas las decisiones pasan por Emanuel. No hay autonomía real en los contributors |

### 3.3. Diagnóstico como Project Lead

> **El equipo está en Fase 0 tardía**. Tienen investigación, tienen plan, tienen diseño. Pero la distancia entre "tener un plan" y "ejecutar el plan" no se ha empezado a recorrer. El riesgo más grande es que la Fase de documentación se alargue tanto que el equipo pierda momentum.

El hecho de que Emanuel haya hecho 14 commits vs 4-11 del resto sugiere que **el coordinador está trabajando EN el proyecto en vez de trabajar SOBRE el proyecto**. Su rol debería ser destrabar, revisar, guiar — no escribir 1.200 líneas de investigación.

---

## 4. Evaluación desde Scrum Master

### 4.1. Lo que funciona

- **Plan de trabajo con sprints**: El timeline consolidado (sprint 1-2, 3-4, etc.) es un buen artefacto de planificación ágil.
- **Definición de "Hecho" (DoD) clara**: El TEAM_CHARTER especifica criterios para código, ML, documentación.
- **Flujo SDD en 8 pasos**: Bien definido en `plan-trabajo.md`.

### 4.2. Lo que no funciona

| Problema | Evidencia |
|----------|-----------|
| **No hay sprints ejecutados** | No hay issues con labels de sprint, no hay milestones, no hay tablero de proyecto |
| **No hay dailies** | El TEAM_CHARTER dice "async vía GitHub antes de las 10am". No hay evidencia de que ocurra |
| **No hay retrospectivas** | No hay documentos de retro. El PR #7 es el primer entregable conjunto y no tuvo review |
| **No hay WIP limits** | Todos trabajan en documentación en paralelo. No hay restricciones de trabajo en progreso |
| **Métricas de equipo ausentes** | No se mide velocity, lead time, cycle time. No hay baseline para mejorar |

### 4.3. La Gran Deuda Ágil

> **El equipo tiene Artefactos Ágiles (plan, DoD, SDD) pero no tiene Ceremonias Ágiles**. Es como tener un auto con ruedas pero sin volante. Los artefactos sin las ceremonias son papel mojado.

**La prioridad #1 desde el rol Scrum Master**: Arrancar el ciclo ágil. Que el equipo sienta el ritmo de un sprint aunque sea de 1 semana. Sin eso, el plan-trabajo es un adorno.

---

## 5. Evaluación desde Product Owner

### 5.1. Valor Entregado

| Aspecto | Evaluación |
|---------|-----------|
| **Visión de producto** | Clara y diferenciada. "Observabilidad predictiva UX-céntrica para recursos escasos" |
| **Personas definidas** | 4 personas con pain points y gains específicos. Buen trabajo de UX research |
| **MVP scope** | Definido y acotado. In-scope vs out-of-scope claro |
| **HU escritas** | Formato INVEST-compliant (criterios de aceptación, pre/postcondiciones) |

### 5.2. Lo que falta

| Problema | Impacto |
|----------|---------|
| **HU no priorizadas** | No hay MoSCoW ni value points. No sé qué es lo más importante para el negocio |
| **HU sin estimación** | No hay story points ni tiempo estimado. El PO no puede planificar releases |
| **Sin validación con usuarios reales** | Las personas están definidas pero no se testeó con SREs estudiantes reales |
| **Sin métricas de éxito del producto** | ¿Cómo sé que IntellOps es exitoso? Más allá de KPIs técnicos, no hay OKRs de producto |

### 5.3. El Problema de la Priorización

> **El plan-trabajo asigna tareas a contributors, pero no hay una pila de producto priorizada por valor de negocio**. Las tareas están organizadas por "Fase 1 → Fase 2", no por "lo que más valor genera primero".

Desde el rol PO, yo preguntaría: **¿Cuál es la métrica más dolorosa para el laboratorio GIDAS hoy?** Probablemente la falta de visibilidad del estado de los servicios. Eso debería ser lo primero que resolvamos — y no está en el plan.

---

## 6. Evaluación Individual: Federico (BlancoCavallero)

### 6.1. Fortalezas

- **Visión de negocio**: El análisis de caso de negocio y las HU muestran que entiende el "para qué" del proyecto. Eso es valioso en un equipo técnico que tiende a enfocarse en el "cómo".
- **Resolución de problemas técnicos**: Los 3 fixes de CI demuestran que puede diagnosticar y resolver issues en un stack que no configuró. Para un proyecto con recursos escasos, tener a alguien que destrabe pipelines es oro.
- **Disciplina de gestión de cambios**: Escribir CONTRIBUTING.md muestra que entiende que la estandarización del flujo de trabajo es tan importante como el código.

### 6.2. Áreas de Mejora

| Aspecto | Situación actual | Recomendación |
|---------|-----------------|---------------|
| **Formato de entregables** | PDFs no versionables | Convertir a Markdown + Mermaid para diagrams |
| **Profundidad técnica** | Solo fixes de CI, sin features nuevas | Arrancar con T1.1 (baseline seguridad) del plan-trabajo |
| **Autonomía** | Dependiente del coordinador para decisiones | Proponer un cambio sin que se lo pidan |
| **Conexión negocio-técnica** | HU genéricas (login/logout) no diferencian IntellOps | Focalizar HU en lo que hace único a IntellOps |
| **Testing de software** | Sin evidencia de práctica de testing | Aplicar TDD en el próximo cambio |

### 6.3. Nota del Project Lead

Federico tiene **perfil de Analista de Negocio + DevOps**. Su valor diferencial es la capacidad de traducir necesidades del laboratorio a especificaciones técnicas. Debería fortalecer el lado práctico (implementar lo que especifica) para no quedar solo en "el que escribe docs".

---

## 7. Evaluación Individual: Romeo (RomeKai)

### 7.1. Fortalezas

- **Pensamiento arquitectónico**: El DER V1.2 con soporte multi-tenant, MLOps, JSONB y confidence_score muestra que piensa en el futuro del sistema, no solo en el MVP. Eso es raro en un contributor inicial.
- **Enfoque en métricas de usuario**: La "traducción psicológica" de las métricas es un approach innovador que conecta datos técnicos con experiencia humana. Diferencia a IntellOps de una solución genérica.
- **Comprensión del ciclo de vida de datos**: Desde la captura (métricas RUM) hasta el almacenamiento (DER) y el consumo (ML, alertas).
- **Calidad sobre cantidad**: Solo 4 commits pero cada uno aporta un artefacto completo y bien pensado.

### 7.2. Áreas de Mejora

| Aspecto | Situación actual | Recomendación |
|---------|-----------------|---------------|
| **Volumen de contribuciones** | 4 commits es poco para el tiempo transcurrido | Acelerar el ritmo de entregas |
| **Formato de entregables** | PDFs sin diff posible | Pasarlos a Markdown + PlantUML para DER |
| **Conexión con implementación** | El DER no está implementado en código | Arrancar con T1.1 (esqueleto ML engine) del plan-trabajo |
| **Revisión del trabajo de otros** | Sin evidencia de reviews | Revisar el trabajo de Federico o Santiago |
| **Documentación de decisiones** | Las justificaciones del DER están en texto, no en ADR | Crear ADR con la decisión del modelo de datos |

### 7.3. Nota del Project Lead

Romeo tiene **perfil de Arquitecto de Datos + ML Engineer**. Su trabajo en el DER y métricas es el mejor equilibrio entre investigación y diseño práctico. Debería ser el primero en pasar a código, implementando el esqueleto ML que diseñó. Su riesgo es el bajo volumen de commits — no porque haga trabajo de mala calidad, sino porque el proyecto necesita más cantidad de iteraciones.

---

## 8. Evaluación Individual: Santiago (Monta702)

### 8.1. Fortalezas

- **Documentación estructurada**: Las 3 versiones de estructura de carpetas muestran que entiende el valor de la documentación organizada.
- **Diagrama C4**: Es el único contributor que generó un artefacto visual de arquitectura. El C4 es estándar de la industria y es valioso para comunicar la arquitectura a stakeholders no técnicos.
- **Investigación de base de datos**: Aunque no está conectada con el DER de Romeo, muestra iniciativa de investigar por su cuenta.
- **Minutas de reuniones**: Registra las reuniones. Eso es infraestructura de comunicación del equipo que nadie más hace.

### 8.2. Áreas de Mejora

| Aspecto | Situación actual | Recomendación |
|---------|-----------------|---------------|
| **Alineación con el equipo** | DB research desconectada del DER de Romeo | Coordinar con Romeo antes de investigar |
| **Formato de entregables** | PDFs sin diff posible | Pasar a Markdown |
| **Volumen de contribución propia** | 6 commits propios vs 3 merges | Más código propio, menos merges |
| **Profundidad técnica** | Sin código ni tests | Arrancar con T1.1 (CI pipeline real) del plan-trabajo |
| **Precisión** | Commits con typos ("pertecence", "dle") | Revisar mensajes de commit antes de pushear |

### 8.3. Nota del Project Lead

Santiago tiene **perfil de QA / Documentation Lead**. Su aporte de infraestructura documental es necesario pero no urgente. Una vez que el proyecto tenga un C4 y una estructura de carpetas, su contribución marginal disminuye. Debería pivotar rápido a tareas de implementación concreta: el pipeline CI/CD real es su mejor próxima tarea. Sus merges frecuentes de la rama `docs/actualizacion` sugieren que está trabajando como "integrador de docs" — rol que debería desaparecer a medida que el equipo aprenda a mergear directo.

---

## 9. Sugerencias de Arquitectura de Software

### 9.1. Problema: Monolito vs Microservicios en Recursos Escasos

**Diagnóstico**: El brief habla de "OTel Collector + FastAPI + Tempo + Loki + Grafana + SQLite + ML + GenIA". Son ~8 servicios diferentes. Para < 2GB RAM, esto va a ajustar.

**Sugerencia**: Adoptar una **arquitectura de monolito modular** en lugar de microservicios:

```
┌─────────────────────────────────────────────────────┐
│                   intellops-app                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────┐   │
│  │ Ingesta  │  │  ML      │  │  GenIA (llama.cpp)│   │
│  │ (FastAPI)│  │ (sklearn)│  │  (proceso aparte) │   │
│  └────┬─────┘  └────┬─────┘  └──────────────────┘   │
│       │              │                               │
│  ┌────▼──────────────▼─────┐                         │
│  │      SQLite (WAL)       │                         │
│  └─────────────────────────┘                         │
│       │                                              │
│  ┌────▼─────┐                                        │
│  │ Dashboard│                                        │
│  │ (React)  │                                        │
│  └──────────┘                                        │
└─────────────────────────────────────────────────────┘
```

**Beneficio**: Un solo `docker compose` service en vez de 8. Menos RAM, menos latencia de red interna, menos complejidad operativa.

**Excepción**: Grafana + Loki + Tempo deben ser servicios separados porque son externos.

### 9.2. Problema: Ausencia de OpenAPI Spec

**Diagnóstico**: El brief menciona OpenAPI 3.1 y AsyncAPI 3.0, pero **no existe ninguna spec**. Sin contract, el equipo no puede implementar en paralelo.

**Sugerencia**: **Antes de escribir una línea de código de lógica de negocio**, definir el contrato:

```yaml
# /specs/openapi.yaml (mínimo)
openapi: 3.1.0
paths:
  /v1/metrics/ingest:     # POST - Recibir métricas del agente
  /v1/metrics/query:      # GET  - Consultar métricas
  /v1/anomalies:          # GET  - Listar anomalías
  /v1/anomalies/detect:   # POST - Ejecutar detección
  /v1/health:             # GET  - Health check
```

**Regla**: Nadie escribe código hasta que la spec esté aprobada. Esto es SDD real, no decorativo.

### 9.3. Problema: Datos de Entrenamiento vs Datos de Producción

**Diagnóstico**: El plan dice "entrenar Isolation Forest sobre SWaT / Yahoo S5". Estos datasets son de plantas industriales y servidores web, no de laboratorio académico. El modelo no va a generalizar.

**Sugerencia**: Generar un **dataset sintético propio** que modele el comportamiento del laboratorio GIDAS:
- Horarios pico (entrada de alumnos, cambios de hora)
- Patrones de uso de servicios específicos
- Estacionalidad semanal / cuatrimestral
- Ruido realista

Esto debería ser el **primer experimento ML**: no Isolation Forest, sino **generación de datos sintéticos**.

### 9.4. Problema: El RUM Agent es Caja Negra

**Diagnóstico**: La investigación de Emanuel propone un agente RUM custom. Eso es un proyecto en sí mismo.

**Sugerencia**: Usar **Grafana Faro** (ex-Grafana Agent for RUM) como SDK base en vez de construir uno propio. Faro ya captura Core Web Vitals, errores JS, trazas OTel, y tiene bundle ~25KB. Lo que no capture Faro se extiende con plugins custom. Reduce el riesgo de implementación a la mitad.

---

## 10. Sugerencias Tecnológicas

### 10.1. Stack Crítico: Base de Datos

| Tecnología actual | Problema | Sugerencia |
|-------------------|----------|------------|
| SQLite + time-index | SQLite no soporta escritura concurrente (WAL ayuda pero no resuelve). Las queries OLAP para ML van a ser lentas | **DuckDB** como capa de analytics. SQLite para ingesta (transaccional) → DuckDB para consultas ML (analítico). DuckDB corre en proceso, < 100MB RAM, y es órdenes de magnitud más rápida para agregaciones |

### 10.2. Stack Crítico: ML Pipeline

| Tecnología actual | Problema | Sugerencia |
|-------------------|----------|------------|
| scikit-learn Isolation Forest | No está diseñado para streaming. Hay que re-entrenar periódicamente | **River** (ML online) o **Tsfresh** para feature extraction sobre series temporales. River está diseñado para data streams y consume < 50MB RAM |
| LSTM como extensión futura | Dependencia de GPU. Si no hay GPU, LSTM es inviable | **Microsoft LightGBM** con gradient boosting. Corre en CPU, es más rápido que LSTM y da resultados comparables en detección de anomalías |

### 10.3. Stack Crítico: Agente RUM

| Tecnología actual | Problema | Sugerencia |
|-------------------|----------|------------|
| Custom RUM Agent | Desarrollar, mantener y optimizar un agente RUM es un proyecto completo | **Grafana Faro SDK** + plugins custom para Rage Clicks y XHR Latency. Faro ya está integrado con el stack Grafana LGTM que eligieron |

### 10.4. Stack Recomendado: Desarrollo

| Capa | Tecnología | Por qué |
|------|-----------|---------|
| **Backend** | FastAPI + Pydantic V2 | Ya está decidido. Bien. Asegurar que el modelo de datos Pydantic refleje el DER |
| **ORM/Lite** | SQLModel | Combina SQLAlchemy + Pydantic. Un solo modelo para DB y API |
| **Dashboard** | React + Vite + D3.js | No cambiar. Pero que el build sea static (sin SSR) para minimizar recursos |
| **Testing** | pytest + pytest-cov + schemathesis | Ya está en el plan |
| **CI/CD** | GitHub Actions | Ya está. Agregar quality gates reales |
| **Container** | Docker Compose | Bien. No migrar a Kubernetes hasta que sea estrictamente necesario |

---

## 11. Sugerencias de Management

### 11.1. Crítica: El Flujo SDD No se Está Usando

**Diagnóstico**: El plan-trabajo define SDD en 8 pasos. El PR #7 no siguió ningún paso de SDD. No hay specs de cambio, no hay ADRs, no hay reviews.

**Sugerencia**: Resetear. Arrancar **Sprint 0** de 1 semana donde:
- El equipo elige **1 tarea** de `plan-trabajo.md`
- **Todos** pasan por el flujo SDD completo: Issue → Spec → Review → Code → PR → Archive
- El coordinador NO codea. Solo review.

### 11.2. Crítica: Ceremonias Ágiles Ausentes

**Diagnóstico**: El TEAM_CHARTER define ceremonias pero no se ejecutan.

**Sugerencia**: Arrancar con **el mínimo ceremonias viable**:

| Ceremonia | Cuándo | Duración | Output |
|-----------|--------|----------|--------|
| **Daily async** | Antes de las 10am | 5 min | Comentario en el issue activo: "qué hice, qué voy a hacer, blockers" |
| **Sprint Planning** | Lunes cada 2 semanas | 30 min | Sprint Goal + issues asignados |
| **Sprint Review** | Viernes cada 2 semanas | 20 min | Demo de lo completado |
| **Retro** | Post-Review | 20 min | "Start / Stop / Continue" |

### 11.3. Crítica: Sin Revisión por Pares

**Diagnóstico**: 0 reviews en el PR #7.

**Sugerencia**: Regla de hierro: **nadie mergea su propio PR**. Mínimo 1 approval. Si no hay approval, no hay merge. Punto.

### 11.4. Crítica: Concentración de Conocimiento en Emanuel

**Diagnóstico**: Emanuel sabe todo. Los demás saben su parte.

**Sugerencia**: **Pair programming sessions obligatorias**:
- Emanuel + Federico: 2 sesiones de 2h para transferir conocimiento del stack FastAPI/OTel
- Emanuel + Romeo: 2 sesiones para transferir conocimiento de ML pipeline
- Emanuel + Santiago: 2 sesiones para transferir conocimiento de CI/CD + testing

Cada sesión debe generar un documento o ADR.

### 11.5. Estandarizar Formato de Entregables

**Diagnóstico**: 14 PDFs que no se pueden diff.

**Sugerencia**: Regla: **No más PDFs**. Todo en Markdown. Diagramas en Mermaid/PlantUML (texto versionable). Si alguien sube un PDF, el PR se rechaza hasta que tenga su versión en Markdown.

---

## 12. Próximos Pasos para el Desarrollo

### 12.1. Sprint 0: Fundación Ejecutable (1 semana)

| Día | Actividad | Responsable |
|-----|-----------|-------------|
| Lunes | Sprint Planning + definir contrato OpenAPI mínimo | **Equipo** |
| Martes | Federico: T1.1 (Lynis baseline) + convertir HU a Markdown | **Federico** |
| Martes | Romeo: Migrar DER a PlantUML + T1.1 (esqueleto ML) | **Romeo** |
| Miércoles | Santiago: T1.1 (CI pipeline real con quality gates) | **Santiago** |
| Jueves | Emanuel: Review de todo + escribir ADR de decisiones de Sprint 0 | **Emanuel** (solo review) |
| Viernes | Sprint Review + Retro | **Equipo** |

### 12.2. Sprint 1-2: Data Pipeline End-to-End (2 semanas)

**Objetivo**: Datos desde el agente hasta la DB, visibles en Grafana.

| Paso | Tarea | Depende de |
|------|-------|------------|
| 1 | Spec OpenAPI: `/v1/metrics/ingest` aprobada | Sprint 0 |
| 2 | Implementar endpoint de ingesta FastAPI | OpenAPI spec |
| 3 | Configurar SQLite con schema del DER V1.2 | Sprint 0 (Romeo) |
| 4 | Script de datos sintéticos para poblar la DB | — |
| 5 | Grafana dashboard conectado a SQLite (vía sqlite-datasource) | — |
| 6 | Demo: POST metric → visible en Grafana | Pasos 1-5 |

### 12.3. Sprint 3-4: Dashboard + Primer Métrica (2 semanas)

**Objetivo**: Las 5 métricas del MVP visibles en el dashboard React.

| Paso | Tarea | Depende de |
|------|-------|------------|
| 1 | Implementar endpoint `/v1/metrics/query` | Sprint 1-2 |
| 2 | Componente React para TTFB (el más simple) | Endpoint query |
| 3 | Componente React para FCP | TTFB funcionando |
| 4 | Mock de Rage Clicks + JS Errors | — |
| 5 | Demo: Dashboard con 2 métricas reales + 3 mock | Pasos 1-4 |

### 12.4. Sprint 5-6: ML Básico + Alertas (2 semanas)

**Objetivo**: Detección de anomalías simple + alerta por Telegram.

| Paso | Tarea | Depende de |
|------|-------|------------|
| 1 | Isolation Forest sobre datos sintéticos | Sprint 1-2 |
| 2 | Endpoint `/v1/anomalies/detect` | ML model |
| 3 | Alerta a Telegram cuando anomaly score > 0.8 | Alertmanager |
| 4 | Demo: "inyectar anomalía" → detectar → alertar | Pasos 1-3 |

### 12.5. Reglas de Oro para Todos los Sprints

1. **Nadie codea sin spec** — Issue → Spec → Review → Code
2. **Cada PR tiene ≥ 1 review** — Sin excepción
3. **Tests antes del código** — TDD aunque sea simple
4. **Sin PDFs** — Markdown o código
5. **El coordinador no codea** — Solo review, guía, destraba

---

*IntellOps — Evaluación del Equipo · Informe de Avance 1 · 2026-07-30*
