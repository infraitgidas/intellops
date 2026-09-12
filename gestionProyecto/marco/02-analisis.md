# IntellOps — Marco Conceptual: Análisis

**Documento**: `02-analisis.md`
**Parte del marco**: Marco Conceptual e Ingenieril de IntellOps
**Versión**: 1.0
**Fecha**: 2026-09-11
**Autor**: Coordinación InfraIT — Emanuel Rodríguez
**Estado**: Borrador para revisión del equipo

---

## 1. Análisis Sistémico del Dominio

### 1.1. El sistema de referencia: IntellOps como sistema de control

Desde una perspectiva de **teoría de sistemas**, IntellOps es un **sistema de control de lazo cerrado**
(retroalimentado) sobre el proceso de producción y operación de software:

```
        ┌─────────────────────────────────────────────────────────────────┐
        │               SISTEMA CONTROLADO (objeto de estudio)            │
        │   Aplicaciones de software + infraestructura IT de GIDAS        │
        │   (y de organizaciones adoptantes)                               │
        └───────────────┬─────────────────────────────────────────────────┘
                        │  Estado real del sistema (señales)
                        ▼
        ┌───────────────────────────────┐
        │   SISTEMA DE MEDICIÓN         │  ← Captura RUM + OTel + infra
        │   (Telemetría: m/l/t, UX)     │
        └───────────────┬───────────────┘
                        │  Datos crudos
                        ▼
        ┌───────────────────────────────┐
        │   SISTEMA DE ANÁLISIS         │  ← AIOps: anomalías, forecast,
        │   (ML + correlación + LLM)    │     health score, RCA
        └───────────────┬───────────────┘
                        │  Diagnóstico / predicción
                        ▼
        ┌───────────────────────────────┐
        │   SISTEMA DE ACCIÓN           │  ← Alertas multicanal, dashboards,
        │   (Alertas + visualización)   │     asistente conversacional
        └───────────────┬───────────────┘
                        │  Retroalimentación
                        ▼
        ┌───────────────────────────────┐
        │   TOMA DE DECISIÓN HUMANA     │  ← Equipo InfraIT, investigadores,
        │   (SRE / coordinación)        │     desarrolladores
        └───────────────────────────────┘
                        │ Actuación correctiva/preventiva
                        ▼
         (vuelve al sistema controlado)
```

**Propiedades sistémicas que debe cumplir IntellOps:**

| Propiedad sistémica | Definición | Requisito para IntellOps |
|---|---|---|
| **Observabilidad** (propiedad del sistema) | El estado interno deducible desde los outputs externos | Toda señal relevante del stack produce telemetría sin instrumentación manual excesiva |
| **Controlabilidad** | Capacidad de actuar sobre el sistema | Alertas accionables, RCA explican *qué* hacer, no solo *qué pasó* |
| **Homeostasis / Resiliencia** | Mantener el servicio ante perturbaciones | Detección temprana → prevención antes del impacto UX |
| **Emergencia** | Comportamientos que surgen de la interacción | La correlación m/l/t + UX exhibe patrones que no se ven por señal aislada |
| **Apertura** | Intercambio con el entorno | Estándares abiertos (OTel, Prometheus), APIs públicas, transferencia al medio |

### 1.2. Entorno del sistema (lo que está fuera y condiciona)

| Factor de entorno | Caracterización | Impacto en IntellOps |
|---|---|---|
| Hardware disponible | Servidores legacy (4-8GB RAM, 2-4 cores), Raspberry Pi, free-tier cloud | Restricción: todo el stack < 2GB RAM, $0/mes |
| Equipo humano | 3 PPS (Federico, Romeo, Santiago) + coordinador + director | 200 hs por PPS; 10 hs/semana c/u; cronogramas 20 semanas |
| Contexto académico | PPS, cátedras, congresos (CACIC, JAIIO), revistas | Cada módulo debe producir insumo publicable |
| Mercado | Datadog, New Relic, Dynatrace, Grafana Cloud, SigNoz, Netdata | Nicho: bajo recurso + alta IA + UX académica |
| Estándares | OpenTelemetry, OAS, AsyncAPI, SLSA, W3C Trace Context | Adopción de estándares = interoperabilidad y ciencia |
| Marco regulatorio/legal | Licencias open source (SSPL ELK → reemplazo por GLP, ADR-0001) | Decisión de licencias ya resuelta: Grafana LGTM |

---

## 2. El Problema (Definición Ingenieril)

**Problema central** (enunciado formal):

> Las organizaciones que construyen y operan software no disponen de una respuesta clara, medible y
> anticipada a la pregunta: **"¿cómo está viviendo nuestro usuario/cliente el producto hoy, y cómo lo va
> a vivir mañana?"** Las herramientas de observabilidad existentes están orientadas a infraestructura y
> a perfiles SRE expertos, tienen costo prohibitivo para pymes/laboratorios académicos, y **no traducen
> la telemetría técnica en valor de negocio comprensible y accionable**.

**Por qué es un problema real y vigente (evidencia del repo):**

1. **El mercado de observabilidad 2026** (brief-v2 §2.1): Datadog ($500K-$2M/año), Dynatrace, New Relic — costos fuera del alcance de pymes y laboratorios; todas orientadas a infra/back-end.
2. **El gap identificado** (brief-v2 §2.2): ninguna plataforma open-source combina (a) hardware modesto, (b) GenIA local, (c) UX académica, (d) $0/mes, (e) reproducibilidad científica.
3. **La investigación propia** (`docs/research/frontend-observability.md`, `rum-agent-deep-dive.md`): el estado del arte de observabilidad frontend (RUM, Core Web Vitals) está maduro técnicamente pero **no está integrado a un marco de decisión de negocio**.
4. **El PID del grupo** (Línea 740): "anticipar fallas y detectar anomalías en entornos dinámicos" — el PID reconoce el desafío; IntellOps lo materializa.

### 2.1. Síntoma vs causa raíz

| Síntoma observable | Causa raíz |
|---|---|
| Reclamos de usuarios por lentitud/errores | No hay visibilidad correlacionada UX→infra; se entera cuando reclama el usuario |
| Alertas ruidosas / alert fatigue | Umbrales fijos sobre señales aisladas, sin contexto UX |
| Downtime que se detecta tarde | Monitoreo clásico verifica disponibilidad, no experiencia |
| Dificultad para justificar inversión en calidad | No hay métricas de impacto del software en el usuario |
| Software académico frágil | Ausencia de QA automatizado y CI/CD (documentado por Santiago en su PPS) |

---

## 3. Stakeholders y sus intereses

| Stakeholder | Rol | Interés principal | Lo que IntellOps le aporta |
|---|---|---|---|
| **Dirección GIDAS** (Ing. Nahuel) | Director del PID | Publicaciones, transferencia, formación RRHH | Prototipo del PID, papers, casos de estudio |
| **Coordinación InfraIT** (Ema) | Coordinador/arquitecto | Coherencia técnica, visión I+D+i | Marco, especificaciones, backlog, gobernanza SDD |
| **Colaboradores PPS** (Federico, Romeo, Santiago) | Desarrolladores | Aprobar PPS (200 hs), portfolio, co-autoría | Módulos con criterios claros, DoD, insumo publicable |
| **Investigadores GIDAS** | Usuarios del sistema | Datos para papers, reproducibilidad | Exportación de datasets, notebooks, specs públicas |
| **Usuarios finales de apps GIDAS** | Visita/uso | Que el sistema funcione bien | IntellOps los protege proactivamente |
| **Adoptantes potenciales** (pymes, otras UTN) | Transferencia | Solución barata y efectiva | Prototipo $0/mes, reproducible < 30 min |
| **Comunidad open source** | Contribución/adopción | Software libre de calidad | Repo público, docs, specs |

---

## 4. Análisis de Mercado y Posicionamiento

### 4.1. Mapa competitivo (fuente: brief-v2 §2.1)

| Plataforma | Modelo | AI/ML | Self-host | Costo anual | Recurso requerido |
|---|---|---|---|---|---|
| Datadog | SaaS | Watchdog + Bits AI | No | $500K-$2M | Alto |
| Dynatrace | SaaS+On-prem | Davis AI | Limitado | $500K+ | Alto |
| Grafana Stack | OSS+Cloud | Plugin-based | Sí | $20K-$80K | Medio-Alto |
| New Relic | SaaS | AI Monitoring | No | $50K-$200K | Medio-Alto |
| SigNoz | OSS+Cloud | Básico | Sí | $30K-$100K | Medio |
| OpenObserve | OSS+Cloud | O2 SRE Agent | Sí | Competitivo | Medio |
| Netdata | OSS+Cloud | ML edge (<5% CPU) | Sí | Bajo | **Bajo** |
| **IntellOps** | **OSS (I+D+i)** | **IF + LLM local** | **Sí** | **$0** | **Bajo** |

### 4.2. Nicho y ventaja diferencial

**IntellOps se posiciona en el cuadrante "Bajo Recurso + Alta IA + UX-céntrica"** — el único con:
1. Operación en hardware modesto (< 2GB RAM, CPU dual-core, sin GPU).
2. GenIA local funcional (LLM cuantizado, sin APIs externas ni costo de inferencia).
3. UX diseñada para usuarios académicos y de negocio (no solo SREs expertos).
4. Costo operativo $0/mes.
5. Reproducibilidad científica (containerizado, specs públicas, datos exportables).
6. **Foco en la experiencia del usuario final como primera clase** (RUM + health score + RCA).

> **La ventaja diferencial de IntellOps frente al mercado no es tecnológica: es de ENFOQUE.**
> Mientras Datadog observa el sistema, IntellOps observa *al usuario del sistema*.

---

## 5. Estudio de Factibilidad

### 5.1. Factibilidad técnica
- Stack probado y open source: OpenTelemetry, Grafana LGTM (Loki/Tempo/Mimir), FastAPI + SQLModel, PostgreSQL, scikit-learn, llama.cpp. *(ADR-0001 ya resuelve la decisión ELK→GLP; ADR-0002 define PostgreSQL como almacenamiento del MVP.)*
- Equipo con capacidad demostrada: 120+ commits, CI funcionando, prototipos de agente RUM ya escritos (`rum-observability`).
- **RIESGO CONTROLADO**: PostgreSQL puro soporta el threshold MVP (1K/s) con holgura; si el volumen crece, TimescaleDB se activa como extensión (ADR-0002).

### 5.2. Factibilidad económica
- Presupuesto PID disponible: $61M ARS (3 años, UTN SCYT) — mayormente RRHH; IntellOps opera con el hardware existente + free-tier ($0/mes de operación, ~$690 USD totales según brief §13).
- **No hay dependencia de licencias comerciales** (GLP reemplaza ELK por licencia SSPL — ADR-0001).

### 5.3. Factibilidad operacional
- 3 colaboradores PPS × 200 hs + coordinación = ~600 hs de desarrollo directo en 2026.
- Cronogramas existentes (20 semanas) compatibles con sprint de 2 semanas del proyecto.
- Infraestructura real del laboratorio como banco de pruebas.

### 5.4. Factibilidad temporal
- Etapa E1 del PID (estado del arte) ya está adelantada por la investigación del grupo.
- IntellOps 2026 (PPS) alimenta E2 (experimentación 2028) y E3 (prototipo 2029).
- Ventana: las PPS 2026 son la oportunidad de construir los cimientos ahora.

---

## 6. Riesgos y Mitigaciones (análisis)

| # | Riesgo | Prob | Impacto | Mitigación |
|---|---|---|---|---|
| R1 | Alcance excesivo para el equipo disponible | Media | Alto | Backlog priorizado (MoSCoW), MVP por fases, DoD estricto |
| R2 | Planes PPS desalineados del marco (ej. ELK vs GLP) | Alta | Alto | **Este marco + revisión de planes**: ver `../equipo/analisis-pps-acoplamiento.md` |
| R3 | PostgreSQL sin tuning puede degradar consultas temporales | Media | Medio | Índices temporales + `EXPLAIN ANALYZE`; TimescaleDB como extensión si el volumen lo exige |
| R4 | LLM 1B insuficiente para RCA complejo | Media | Medio | Fallback templates; fine-tuning futuro; eval de precisión factual ≥80% |
| R5 | Hardware legacy falla | Baja | Alto | Backup diario S3 free-tier; compose para rebuild < 30 min |
| R6 | Free-tier expira (AWS 12 meses) | Media | Medio | Migrar a GCP/Azure free-tier o self-host completo |
| R7 | Alert fatigue / dashboards no usados | Media | Medio | Métricas de uso del dashboard, personas definidas, diseño UX propio |
| R8 | Datos académicos sensibles | Medio | Alto | Seguridad por diseño (hardening CIS, SIEM ligero, OWASP) |
| R9 | Comunidad/transferencia baja | Media | Medio | Publicaciones, demos, dashboard público read-only anonimizado |

---

## 7. Preguntas abiertas para el equipo (a resolver en taller)

1. ¿Validamos "UX-céntrico" como posicionamiento oficial del PID o es una línea del grupo InfraIT?
2. ¿El MVP 2026 debe priorizar RUM+HealthScore (Romeo+Ema) o infraestructura primero (Federico/Santiago)?
3. ¿Adoptamos el User Health Score como "moneda común" de valor hacia el negocio?
4. ¿Qué métricas concretas exige la organización/cliente para el "valor diferencial" (SLA, CSAT, NPS, MTTR)?

---

## 8. Siguiente Documento

→ `03-diseno.md` — diseño sistémico: arquitectura, ciclo de control, componentes y stack.

*Documento vivo.*