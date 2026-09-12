# IntellOps — Marco Conceptual: Objetivo

**Documento**: `01-objetivo.md`
**Parte del marco**: Marco Conceptual e Ingenieril de IntellOps (objetivo, análisis, diseño, especificaciones)
**Versión**: 1.0
**Fecha**: 2026-09-11
**Autor**: Coordinación InfraIT — Emanuel Rodríguez
**Estado**: Borrador para revisión del equipo

---

## 1. Propósito del Documento

Definir el **objetivo macro** de IntellOps de forma clara, ingenieril y sistémica, enmarcándolo en el PID
de Observabilidad al que pertenece (GIDAS · UTN FrLP). Este documento es la piedra angular del marco
conceptual: todo análisis, diseño, especificación y backlog posterior deriva de aquí.

---

## 2. Contexto Institucional: El PID de Observabilidad

IntellOps no es un proyecto aislado: es la **materialización de producto** del PID

> **PID TC (Incentivado) — "Observabilidad de Infraestructura IT en la era de Producción de Software asistido por IA: métodos y plataformas tecnológicas"**
> | Campo | Valor |
> |---|---|
> | Código / Convocatoria | Convocatoria 2026 — PID Equipos Consolidados |
> | Facultad | UTN Facultad Regional La Plata |
> | UCT | GIDAS — Grupo de Investigación y Desarrollo Aplicado a Sistemas Informáticos y Computacionales |
> | Director | Ing. Eduardo Leopoldo Nahuel |
> | Co-director | Leandro Rocca |
> | Duración | 3 años — 01/04/2027 al 31/03/2030 |
> | Actividad | Investigación Aplicada |

**Objetivo general del PID** (fuente: formulario PID, Línea 719):

> Generar un prototipo de plataforma tecnológica que combine **observabilidad avanzada con Inteligencia
> Artificial** en infraestructuras IT híbridas y distribuidas, con el fin de optimizar la detección de cuellos
> de botella, anticipar fallas y mejorar la eficiencia, confiabilidad y agilidad en los procesos de producción
> de software.

**Objetivos específicos del PID** (Líneas 732-754):

| # | Objetivo específico |
|---|---|
| OE1 | Diseñar metodologías de recolección y correlación de métricas, logs y trazas en infraestructuras IT híbridas y distribuidas, orientadas a comprender el comportamiento interno de sistemas complejos. |
| OE2 | Explorar técnicas de IA aplicadas a operaciones de TI (AIOps) para anticipar fallas y detectar anomalías en entornos dinámicos de producción de software. |
| OE3 | Integrar estándares abiertos de observabilidad en el marco de trabajo del prototipo (OpenTelemetry, Prometheus, Grafana, ELK), favoreciendo trazabilidad y métricas unificadas en microservicios y contenedores. |
| OE4 | Evaluar el impacto potencial del prototipo en la eficiencia, confiabilidad y agilidad de los procesos de producción de software (empresas, pymes, laboratorios académicos como GIDAS). |

**Etapas del PID** (cronograma oficial):

| Etapa | Período | Foco |
|---|---|---|
| **E1 — Estado del arte y exploración** | 2027 | Relevamiento bibliográfico, estándares, diseño metodológico, ensayos exploratorios |
| **E2 — Experimentación y validación** | 2028 | AIOps, correlación m/l/t, validación de técnicas, evaluación de impacto en UX |
| **E3 — Prototipado y transferencia** | 2029 | Implementación del prototipo, escalabilidad, transferencia, publicaciones, PI |

---

## 3. Objetivo Macro de IntellOps

### 3.1. Declaración de Objetivo

> **IntellOps** es un **sistema de observabilidad predictiva centrado en la experiencia del usuario (UX)**
> que responde a la pregunta: *"¿cómo está viviendo el usuario/cliente el producto de software que su
> organización construye y opera?"*.
>
> IntellOps captura, correlaciona y analiza **métricas concretas del frontend** — performance,
> disponibilidad, latencia, errores y experiencia real de uso — junto con señales de la infraestructura que
> lo sostiene, y aplica Inteligencia Artificial para **anticipar fallas antes de que el usuario las padezca**,
> generando **valor diferencial medible para la organización**: menos reclamos, mejor percepción de
> calidad, y decisiones basadas en evidencia sobre el producto software.

### 3.2. La tesis diferencial: del "qué ocurre en infra" al "cómo lo vive el usuario"

El monitoreo clásico y gran parte del mercado de observabilidad responde: *"¿está el servidor caído?"*.
El enfoque clásico de infraestructura (propio del monitoreo) mira **servidores, CPU, memoria, red**.

**IntellOps invierte la perspectiva**: el usuario es el sistema de referencia. La infraestructura importa
en la medida en que degrada la experiencia. IntellOps articula **tres capas de señales**:

```
┌────────────────────────────────────────────────────────────────────┐
│  CAPA 1 · EXPERIENCIA (Frontend / RUM)                              │
│  Core Web Vitals: LCP, INP, CLS · TTFB · errores de frontend ·     │
│  sesiones · journeys de usuario                                     │
├────────────────────────────────────────────────────────────────────┤
│  CAPA 2 · PRODUCTO (Backend / Servicios)                            │
│  Latencia p95/p99 · throughput · error rate · trazas distribuidas  │
│  (OpenTelemetry) · SLOs de servicio                                 │
├────────────────────────────────────────────────────────────────────┤
│  CAPA 3 · INFRAESTRUCTURA (Hosts / Contenedores)                    │
│  CPU, memoria, red, disco · logs de seguridad · hardening CIS      │
│  (Grafana + Loki + Prometheus, reemplazando ELK — ver ADR-0001)    │
└────────────────────────────────────────────────────────────────────┘
        │
        ▼
  CORRELACIÓN + IA (AIOps)
  Detección de anomalías · forecasting · health score de usuario ·
  clasificación de reclamos · RCA asistida por LLM local
        │
        ▼
  ACCIÓN
  Alertas multicanal · dashboards · asistente conversacional ·
  retroalimentación al backlog de desarrollo
```

El **valor diferencial** no está en ninguna capa aislada: está en la **cadena causal**
`experiencia → producto → infraestructura` correlacionada y explicada por IA.

### 3.3. Objetivo General de IntellOps

> **Diseñar e implementar IntellOps**: una plataforma de observabilidad predictiva centrada en el usuario
> que integre telemetría de experiencia de usuario (frontend), señales de producto e infraestructura,
> procesamiento con IA (AIOps) y mecanismos de acción (alertas, dashboards, asistente), orientada a
> operar en entornos de recursos escasos (hardware on-premise + free-tier cloud), generando valor
> diferencial medible para la organización sobre el producto software y aportando metodologías,
> datos experimentales y publicaciones científicas al PID de Observabilidad de GIDAS.

### 3.4. Objetivos Específicos de IntellOps

| # | Objetivo específico de IntellOps | Alineación con PID |
|---|---|---|
| IO1 | Capturar métricas de experiencia de usuario (RUM): LCP, INP, CLS, TTFB, errores de frontend, journeys, con overhead mínimo (< 3%) y bundle < 30KB. | OE1 |
| IO2 | Construir el pipeline de ingesta, almacenamiento y consulta de telemetría (métricas, logs, trazas) con estándares abiertos (OpenTelemetry, Prometheus exposition, Grafana LGTM), en recursos escasos. | OE1, OE3 |
| IO3 | Detectar anomalías y anticipar fallas con IA (Isolation Forest + estadísticos como baseline; LSTM como extensión), sobre series temporales de las tres capas de señales. | OE2 |
| IO4 | Generar indicadores de salud del usuario (User Health Score) y clasificación predictiva de reclamos, conectando la telemetría con el impacto en el negocio. | OE2, OE4 |
| IO5 | Proveer mecanismos de acción: alertas multicanal (mail, Telegram, WhatsApp) con routing por severidad, dashboards de las tres capas, y asistente de RCA con LLM local + RAG. | OE2, OE4 |
| IO6 | Implementar seguridad por diseño (hardening CIS, observabilidad de eventos de seguridad) y calidad verificable (CI/CD, tests, quality gates) como habilitantes del sistema completo. | OE3, OE4 |
| IO7 | Evaluar el impacto del prototipo en eficiencia, confiabilidad y agilidad de procesos de software, documentando resultados publicables (papers, casos de estudio). | OE4 |

### 3.5. Límites del objetivo (Out of Scope)

| Fuera de alcance | Razón |
|---|---|
| APM de terceros en producción externa | Foco en apps/servicios del laboratorio GIDAS |
| GPU para entrenamiento pesado | Recursos escasos: CPU + modelos cuantizados |
| Mobile app nativa | Dashboard web responsive; PWA como extensión futura |
| Logs no estructurados masivos | Foco en métricas y trazas; logs planos fuera del MVP |
| Integraciones enterprise (Jira/ServiceNow) | Webhooks genéricos |
| LSTM/Prophet en el MVP inicial | Requiere más recursos; se documentan como extensión |

---

## 4. Principios Rectores del Objetivo

1. **El usuario es la referencia del sistema** — toda señal de infraestructura se valida contra la experiencia.
2. **Valor diferencial > feature parity** — no competimos con Datadog en features; competimos en enfoque UX con recursos escasos.
3. **Recursos escasos como restricción de diseño, no como excusa** — $0/mes de operación, hardware legacy + free-tier.
4. **Estándares abiertos primero** — OpenTelemetry, OAS 3.1, AsyncAPI 3.0, Prometheus, SLSA.
5. **SDD (Spec-Driven Development)** — sin spec, no hay código; contrato > implementación.
6. **Ciencia abierta y reproducible** — papers, datos exportables, experimentos versionados.

---

## 5. Éxito del Objetivo (KPIs Macro)

| Dimensión | KPI macro | Target |
|---|---|---|
| Experiencia | Tiempo hasta detectar anomalía que impacta UX | < 10 s |
| Experiencia | User Health Score correlacionado con reclamos reales | r > 0.75 |
| Producto | Tiempo medio de detección de degradación (p99 latencia) | < 10 s |
| IA | F1 detección de anomalías (baseline Isolation Forest) | ≥ 0.70 |
| IA | Precisión factual del RCA asistido por LLM | ≥ 80% |
| Calidad | Cobertura de tests en módulos críticos | ≥ 70% |
| Seguridad | Lynis compliance post-hardening | ≥ 70% |
| Operación | Costo operativo mensual | $0 |
| Científico | Publicaciones / casos de estudio | 1+ por fase |

---

## 6. Declaración de Coherencia con el PID

IntellOps **implementa** el PID de Observabilidad en su dimensión de producto:

- **E1 del PID** (estado del arte) → ya ejecutada parcialmente: `docs/research/*`, `docs/brief-v2.md`, papers de divulgación.
- **E2 del PID** (experimentación) → es donde IntellOps está aportando hoy con las PPS 2026 (detección de anomalías, QA, seguridad).
- **E3 del PID** (prototipo) → IntellOps evolucionará al prototipo de plataforma de observabilidad asistida por IA del PID.

Esto significa que el **cronograma de IntellOps anticipa las etapas del PID**: lo que hoy se prototipa
en el laboratorio GIDAS con recursos escasos, será la plataforma que el PID formalice y transfiera al
medio socio-productivo entre 2027 y 2030.

**Implicancia directa para las PPS**: los planes de trabajo de los colaboradores deben escribirse en el
lenguaje y la arquitectura de este marco (ver `../equipo/analisis-pps-acoplamiento.md`), para que cada
contribución de 200 horas sea un ladrillo verificable del mismo edificio.

---

## 7. Siguiente Documento

→ `02-analisis.md` — análisis sistémico del dominio, el problema, stakeholders, mercado y valor diferencial.

*Documento vivo. Se actualiza con aprobación del coordinador y revisión del equipo.*