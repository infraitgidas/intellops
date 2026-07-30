Voy a realizar una investigación exhaustiva actualizada para redefinir el PI+D+i IntellOps con rigor científico y alineación a recursos escasos.
 
 
 Ahora presento el **Brief del Proyecto IntellOps Redefinido**, producto del análisis exhaustivo del caso de negocio, estado del arte, investigación activa, productos del mercado, proyectos open-source, marcos de trabajo y estándares de la industria IT — todo alineado a la **ingeniería de recursos escasos** (hardware on-premise de bajo rendimiento + servicios cloud free-tier).

---

# Brief del Proyecto IntellOps Redefinido
## Sistema de Observabilidad Predictiva con ML y GenIA para Infraestructura Tecnológica
### Enfoque: Ingeniería de Recursos Escasos + UX-Centric + OpenSpec

---

**Código del Proyecto:** GIDAS-InfraIT-2026-IntellOps  
**Línea de Investigación:** Sistemas Inteligentes de Infraestructura IT — Ingeniería de Recursos Escasos  
**Grupo:** GIDAS (Grupo de Investigación y Desarrollo Aplicado a Sistemas Informáticos y Computacionales)  
**Unidad Académica:** UTN Facultad Regional La Plata (UTN-FRLP)  
**Sub-proyecto:** InfraIT  
**Responsable Técnico:** Equipo de Investigación InfraIT  
**Fecha:** Mayo 2026  
**Versión:** 2.0 (Redefinición Post-Análisis)  

---

## 1. Resumen Ejecutivo

IntellOps es un proyecto de investigación, desarrollo e innovación (PI+D+i) que diseña e implementa un **sistema de observabilidad predictiva minimal viable y evolutivo**, diseñado explícitamente para operar en **hardware on-premise de bajo rendimiento** (servidores legacy reutilizados, Raspberry Pi) complementado con **servicios cloud de free-tier** (AWS, GCP, Azure). El sistema integra modelos de Machine Learning livianos (Isolation Forest + estadísticos, con LSTM como extensión futura) con un asistente de Generative AI local (LLM cuantizado en CPU) y una interfaz de usuario centrada en 4 personas académicas definidas.

El proyecto se desarrolla en el laboratorio GIDAS de la UTN-FRLP con proyección como **herramienta de extensión universitaria** y publicación científica en venues IEEE/ACM. La metodología combina **Spec-Driven Development (SDD)**, **Agile (Scrum/Kanban híbrido)** y **DevOps (CI/CD con GitHub Actions + Docker Compose)** bajo el estándar **OpenSpec (OpenAPI 3.1 + AsyncAPI 3.0)**.

---

## 2. Análisis del Caso de Negocio y Estado del Arte

### 2.1 El Mercado de Observabilidad 2026

En 2026, el mercado de observabilidad se ha consolidado alrededor de **OpenTelemetry** como estándar de instrumentación. Las plataformas compiten en arquitectura de almacenamiento, query performance, correlación de señales y costo. 

| Plataforma | Modelo | AI/ML | Self-Host | Costo Anual (est.) | Recursos Requeridos |
|------------|--------|-------|-----------|-------------------|---------------------|
| **Datadog** | SaaS | Watchdog AI + Bits AI | No | $500K-$2M | Alto (cloud-only) |
| **Dynatrace** | SaaS + On-prem | Davis AI (causal) | Limitado | $500K+ | Alto |
| **Grafana Stack** | OSS + Cloud | Plugin-based | Sí | $20K-$80K self-host | Medio-Alto |
| **New Relic** | SaaS | AI Monitoring | No | $50K-$200K | Medio-Alto |
| **Signoz** | OSS + Cloud | Básico | Sí | $30K-$100K | Medio |
| **OpenObserve** | OSS + Cloud | O2 SRE Agent | Sí | Competitivo | Medio |
| **Netdata** | OSS + Cloud | ML at edge (<5% CPU) | Sí | Bajo | **Bajo** |
| **Uptrace** | OSS + Cloud | AI-driven insights | Sí | Bajo | Medio-Bajo |

### 2.2 Nicho Identificado: El Vacío del "Bajo Recurso + Alta AI"

**El gap detectado**: Ninguna plataforma open-source combina nativamente:
1. **Operación en hardware modesto** (< 2GB RAM, sin GPU, CPU dual-core)
2. **GenIA local funcional** (sin dependencia de APIs externas ni costos de inferencia)
3. **UX diseñada para usuarios académicos** (no enterprise SREs)
4. **Costo operativo $0/mes** (self-hosted + free-tier cloud)
5. **Reproducibilidad científica** (stack containerizado, specs públicas, datos exportables)

**IntellOps se posiciona en el cuadrante "Bajo Recurso + Alta AI"** del mapa de posicionamiento, un nicho inexplorado por las soluciones existentes.

### 2.3 Investigación Activa y Proyectos Relacionados

El estado del arte en 2026 muestra las siguientes líneas de investigación activas: 

- **AIOps académico**: Google SRE, Microsoft Research y Dynatrace investigan ML para detección de anomalías y RCA causal
- **Edge ML para observabilidad**: Netdata demuestra inferencia ML en edge con <5% CPU y 150MB RAM, con 18 modelos unsupervised por métrica 
- **LLM para SRE**: GitHub Copilot for Ops, Amazon Q y proyectos académicos exploran auto-remediación con LLMs
- **eBPF para observabilidad kernel**: Cilium, Pixie (CNCF) y Falco habilitan observabilidad sin instrumentación manual
- **Kubernetes ligero para edge**: K3s y MicroK8s corren en Raspberry Pi 4B con 512MB RAM, validados en investigación de campo 

### 2.4 Estándares de la Industria 2026

| Estándar | Organización | Uso en IntellOps |
|----------|-------------|------------------|
| **OpenTelemetry** | CNCF (graduated) | Instrumentación vendor-neutral de metrics, logs, traces |
| **OpenAPI 3.1** | OpenAPI Initiative | Especificación de APIs REST (contract-first) |
| **AsyncAPI 3.0** | Linux Foundation | Especificación de APIs event-driven (Kafka, WebSocket)  |
| **Prometheus Exposition Format** | CNCF | Formato de métricas para scraping |
| **W3C Trace Context** | W3C | Propagación de traces distribuidos |
| **CloudEvents** | CNCF | Estandarización de eventos cloud |
| **SLSA** | OpenSSF | Seguridad de supply chain |
| **OWASP Top 10 / API Security** | OWASP | Seguridad de aplicaciones web y APIs |

---

## 3. Redefinición del Objetivo General

> **Objetivo General Redefinido:**
>
> Diseñar e implementar un **prototipo funcional minimal viable y evolutivo** del sistema IntellOps para observabilidad predictiva de infraestructura tecnológica, operando en **hardware on-premise de bajo rendimiento** (servidores legacy reutilizados, Raspberry Pi) y **servicios cloud de free-tier**, integrando modelos de Machine Learning livianos (Isolation Forest + estadísticos) con un asistente de Generative AI local (LLM cuantizado en CPU) y una interfaz de usuario centrada en la experiencia de 4 personas académicas definidas, generando documentación técnica, un informe de resultados y un paper científico con potencial de publicación en venues IEEE/ACM.

### 3.1 Cambios Clave respecto a la Versión 1.0

| Aspecto | Versión 1.0 | Versión 2.0 (Redefinido) |
|---------|-------------|--------------------------|
| **Hardware objetivo** | Servidores dedicados con GPU | Hardware on-premise existente + Pi + free-tier cloud |
| **Base de datos** | TimescaleDB (requiere PostgreSQL) | SQLite con time-index (migrable a TimescaleDB) |
| **ML models** | LSTM + Isolation Forest + Prophet | Isolation Forest + estadísticos (LSTM como extensión futura) |
| **GenIA** | Llama 3.1 8B (requiere ~8GB RAM) | Llama 3.2 1B GGUF 4-bit (~600MB RAM, CPU-only) |
| **Backend** | FastAPI + Redis + Kafka | FastAPI + SQLite buffer (sin Redis/Kafka inicialmente) |
| **Dashboard** | React + WebSocket real-time | React static build + polling (sin SSR, sin WebSocket server) |
| **Costo operativo** | ~$500/mes (self-hosted) | **$0/mes** (existente + free-tier) |
| **Setup time** | Horas | **< 30 min** (`docker compose up`) |

---

## 4. Scope del Producto Final Redefinido

### 4.1 Dentro del Alcance (In-Scope)

| Módulo | Descripción | MVP |
|--------|-------------|-----|
| **Agente de Captura** | JS/Node OpenTelemetry, 50KB bundle, sampling 10%, batch 30s | MVP-0 |
| **Ingesta** | FastAPI async, SQLite buffer, batch insert, < 100MB RAM | MVP-0 |
| **Storage** | SQLite con índice temporal, WAL mode, ~500MB/año datos, migrable a TSDB | MVP-0 |
| **Agente RUM OTel** | JS OpenTelemetry SDK, bundle < 30KB, captura Core Web Vitals + trazas + errores de frontend | MVP-1 |
| **OTel Collector** | Recepción y enrutamiento de señales OTel (trazas, métricas, logs) desde agentes RUM y servicios instrumentados | MVP-1 |
| **Tracing (Tempo)** | Almacenamiento y consulta de trazas distribuidas con integración nativa OTel, correlación trace→log→metric | MVP-1 |
| **ML Detection** | Isolation Forest (scikit-learn) + Z-score dinámico + seasonal decomposition, < 50MB RAM | MVP-1 |
| **Dashboard** | React static build, 3 vistas (latencias, heatmap, predicciones), D3.js lightweight, < 1MB bundle | MVP-1 |
| **GenIA Assistant** | Llama 3.2 1B (llama.cpp), RAG con documentación GIDAS, chat en dashboard, 5-10 tok/s en CPU | MVP-1 |
| **Alertas Multicanal** | Grafana Alertmanager con routing a Mail, Telegram y WhatsApp según severidad | MVP-1 |
| **Alertas** | Threshold rules + ML score > 0.8, webhooks a Discord/Slack, email (free SMTP) | MVP-1 |
| **Backup** | Rclone sync a S3 free-tier, incremental diario, 5GB limit | MVP-1 |
| **Self-Monitoring** | Netdata (< 5% CPU, 150MB RAM), auto-discovery, per-second metrics | MVP-1 |
| **Specs** | OpenAPI 3.1 + AsyncAPI 3.0, contract testing, auto-docs | Continuo |
| **Documentación** | Markdown + auto-generated (Redocly), notebooks Jupyter exportables | MVP-2 |
| **Paper Científico** | IEEE/ACM format, reproducible experiments | MVP-2 |

### 4.2 Fuera del Alcance (Out-of-Scope)

| Ítem | Razón |
|------|-------|
| LSTM/Prophet (inicial) | Requieren GPU o RAM > 4GB; se implementan como extensión futura cuando recursos lo permitan |
| Redis/Kafka | Añaden complejidad operativa y RAM; SQLite buffer es suficiente para < 1K métricas/seg |
| TimescaleDB (inicial) | Requiere PostgreSQL dedicado; SQLite es suficiente para datasets < 10GB |
| GPU para ML/GenIA | Costo prohibitivo; todo en CPU con modelos cuantizados |
| APM en producción real | Foco en tracing de apps del laboratorio GIDAS, no en APM de terceros |
| Mobile app nativa | Dashboard responsive web es suficiente; PWA como mejora futura |
| Integración con Jira/ServiceNow | Webhooks genéricos son suficientes; integraciones específicas como extensión |
| Logs no estructurados | Foco en métricas y traces estructurados; logs planos fuera de alcance inicial |

### 4.3 Extensión Futura (Post-MVP)

| Extensión | Requisito de Recursos | Timeline estimado |
|-----------|----------------------|-------------------|
| LSTM para series temporales | GPU o RAM > 8GB | Sem 25-36 |
| TimescaleDB migration | Servidor dedicado PostgreSQL | Sem 25-30 |
| Redis para caching | RAM adicional 2GB | Sem 20-25 |
| Kafka para streaming | Infraestructura adicional | Sem 30-40 |
| Tracing multi-cluster | Tempo federado entre laboratorios GIDAS | Sem 25-30 |
| PWA mobile | Sin requisitos adicionales | Sem 20-25 |

---

## 5. Características del Producto Redefinidas

### 5.1 Core: Observabilidad Predictiva UX-Céntrica

- **Stack LGTM completo**: Grafana + Loki + Tempo + Mimir, el estándar de la industria para observabilidad open-source
- **OpenTelemetry como columna vertebral**: Instrumentación vendor-neutral de métricas, logs y trazas desde frontend hasta backend
- **Agente RUM ultra-liviano**: JS OTel SDK < 30KB que captura Core Web Vitals (LCP, INP, CLS), trazas distribuidas y errores de frontend
- **Tracing distribuido con Tempo**: Correlación traza→log→métrica para entender el viaje completo de cada request de usuario
- **Storage SQLite optimizado**: Índice temporal, WAL mode, migración transparente a TimescaleDB
- **Detección ML liviana**: Isolation Forest + estadísticos (Z-score, seasonal decomposition) en < 50MB RAM
- **Alertas inteligentes multicanal**: Threshold + ML score con routing dinámico a Mail, Telegram y WhatsApp según severidad
- **3 vistas esenciales**: Latencias en tiempo real, mapa de calor de usuarios, predicciones con forecasting

### 5.2 Differentiator: GenIA Local Funcional

- **LLM**: Llama 3.2 1B en formato GGUF 4-bit, ejecutado vía llama.cpp
- **Footprint**: ~600MB RAM, inferencia en CPU a 5-10 tokens/segundo
- **RAG**: Vectorización de documentación GIDAS, runbooks históricos y métricas correlacionadas
- **Capacidades**:
  - RCA en lenguaje natural ("¿Por qué subió la latencia?")
  - Forecasting conversacional ("¿Predice fallas para mañana?")
  - Explicación de anomalías para usuarios no técnicos
  - Generación de runbooks a partir de incidentes resueltos

### 5.3 UX: Centrado en 4 Personas Académicas

| Persona | Rol | Pain Point | Gain de IntellOps |
|---------|-----|-----------|-------------------|
| **SRE Estudiante** | Administra servicios, no experto en ML | Alert fatigue, dashboards incomprensibles | Auto-RCA en lenguaje natural, explicaciones contextuales |
| **Docente/Investigador** | Publica papers, necesita reproducibilidad | Configuración compleja, datos no exportables | One-click export de datasets, notebooks listos, specs públicas |
| **Admin Infraestructura** | Gestiona 20+ servicios, sin tiempo para dashboards | Context switching entre herramientas | Single pane of glass (mapa de calor), mobile-first |
| **Visitante/Extensión** | Ve demo del laboratorio, sin acceso a sistemas | Sin visibilidad del valor del laboratorio | Dashboard público read-only con datos anonimizados |

### 5.4 Principios UX para Recursos Escasos

1. **Progressive Disclosure**: Mostrar solo lo esencial; detalles técnicos bajo toggle "Advanced"
2. **Immediate Feedback**: Cada acción tiene respuesta visual en < 200ms (skeleton screens, spinners)
3. **Offline-First**: Dashboard funciona sin conexión; sync cuando vuelve red
4. **Text-over-Charts**: Para recursos escasos, texto explicativo > visualización pesada
5. **Voice/Chat First**: GenIA como interfaz primaria para usuarios no técnicos
6. **Contextual Help**: Tooltips inteligentes que explican términos técnicos en lenguaje natural
7. **Mobile-First**: 60% de usuarios académicos acceden desde celular
8. **Battery-Aware**: Para edge devices, reducir polling cuando batería < 20%

---

## 6. Atributos de Calidad Redefinidos

### 6.1 Atributos de Calidad del Software (ISO/IEC 25010)

| Atributo | Definición en IntellOps | Target | Métrica |
|----------|------------------------|--------|---------|
| **Disponibilidad** | Sistema operativo 24/7 en hardware modesto | > 99.5% | Uptime monitoring vía Netdata |
| **Escalabilidad** | Capacidad de crecer cuando recursos aumentan | 1K → 10K métricas/seg | Benchmarks con datos sintéticos |
| **Seguridad** | OWASP Top 10 compliant, datos sensibles protegidos | Sin vulnerabilidades críticas | OWASP ZAP + audit manual |
| **Usabilidad** | SUS para 4 personas definidas | > 75 | Cuestionario post-test (n=10) |
| **Mantenibilidad** | Código limpio, testeable, documentado | Coverage > 80% | pytest + coverage report |
| **Portabilidad** | Migración transparente entre entornos | Setup < 30 min | `docker compose up` timing |
| **Reproducibilidad** | Cualquier investigador puede reconstruir el sistema | 100% specs cubiertas | ADRs + OpenAPI + AsyncAPI |
| **Costo-Eficiencia** | Costo operativo mensual | $0/mes | Tracking de gastos cloud |

### 6.2 Atributos de Calidad del Proceso I+D+i

| Atributo | Definición | Target | Métrica |
|----------|-----------|--------|---------|
| **Rigor Científico** | Métodos reproducibles, datos versionados | Paper publicable | Peer review interno |
| **Transferibilidad** | Replicación en otros laboratorios UTN | 2+ laboratorios pilotos | Acuerdos de transferencia |
| **Documentación Viva** | Docs sincronizadas con código | 100% specs actualizadas | CI/CD valida drift |
| **Transparencia** | Código y datos abiertos | GitHub público | Stars + forks + issues |
| **Sostenibilidad** | Mantenimiento post-proyecto | Comunidad activa | Contributors + releases |

---

## 7. Marco Metodológico: SDD + Agile + DevOps + OpenSpec

### 7.1 Spec-Driven Development (SDD)

Aplicado en su modalidad **Spec-Anchored** para proyectos de I+D+i: 

| Fase SDD | Actividad | Artefacto |
|----------|-----------|-----------|
| **Spec-First** (Sem 1-2) | Discovery, user research, análisis competitivo | PRD, OpenAPI 3.1 draft, AsyncAPI 3.0 draft |
| **Spec-Anchored** (Sem 3-20) | Desarrollo guiado por specs, contract testing | Specs versionadas en `/specs/`, codegen, tests de contrato |
| **Spec-as-Source** (Sem 21-24) | Publicación de specs como API pública | Specs en repo público, SDKs generados |

**Beneficios de OpenAPI + AsyncAPI**: 
- Machine-readable contracts para agentes IA
- Code generation evita errores manuales (oapi-codegen)
- Contract testing garantiza compatibilidad (schemathesis)
- Documentación siempre sincronizada con código (Redocly)
- Vendor-neutral (no lock-in)

### 7.2 Agile: Scrum + Kanban Híbrido

| Ritmo | Actividad | Duración |
|-------|-----------|----------|
| **Sprint** | 2 semanas, con planning, daily, review, retro | Continuo |
| **Design Sprint** | Fase 0 (Discovery), validación con usuarios | 1 semana intensiva |
| **Kanban** | Fase 2 (Build), flujo continuo con WIP limits | Sem 7-14 |
| **Lean UX** | Fase 3 (Validate), testing con usuarios reales | Sem 15-18 |

### 7.3 DevOps: CI/CD + Docker + GitOps

```yaml
# Pipeline GitHub Actions
name: IntellOps CI/CD
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Contract Testing
        run: schemathesis run /specs/openapi.yaml --base-url=http://localhost:8000
      - name: Unit Tests
        run: pytest --cov=src --cov-report=xml
      - name: Integration Tests
        run: pytest tests/integration/
  build:
    needs: test
    steps:
      - name: Docker Build
        run: docker build -t intellops:${{ github.sha }} .
      - name: Push to Registry
        run: docker push intellops:${{ github.sha }}
  deploy:
    needs: build
    if: github.ref == 'refs/heads/main'
    steps:
      - name: Deploy to Lab
        run: docker-compose -f docker-compose.prod.yml up -d
      - name: Health Check
        run: curl -f http://lab-gidas:8000/health
```

### 7.4 OpenSpec: OpenAPI 3.1 + AsyncAPI 3.0

```yaml
# /specs/openapi.yaml (extracto)
openapi: 3.1.0
info:
  title: IntellOps API
  version: 1.0.0
  description: API de observabilidad predictiva para infraestructura GIDAS
paths:
  /metrics/ingest:
    post:
      summary: Ingesta de métricas OTel
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/MetricBatch'
      responses:
        '202': { description: Métricas aceptadas }
  /anomalies/detect:
    get:
      summary: Detección de anomalías
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/AnomalyList'
```

```yaml
# /specs/asyncapi.yaml (extracto)
asyncapi: 3.0.0
info:
  title: IntellOps Events
  version: 1.0.0
channels:
  anomaly/detected:
    address: anomaly/detected
    messages:
      anomalyEvent:
        payload:
          type: object
          properties:
            metric: { type: string }
            score: { type: number }
            timestamp: { type: string, format: date-time }
```

---

## 8. Stack Tecnológico Redefinido para Recursos Escasos

| Capa | Tecnología | Alternativa descartada | Justificación |
|------|-----------|----------------------|---------------|
| **Agente RUM** | OpenTelemetry JS SDK (< 30KB) | Agentes propietarios | Estándar CNCF, vendor-neutral, Core Web Vitals + trazas |
| **OTel Collector** | OpenTelemetry Collector (Go) | Export directo | Recepción unificada OTLP, procesamiento y enrutamiento |
| **Backend** | FastAPI + Uvicorn | Django, Flask | Async nativo, auto-docs OpenAPI, < 100MB RAM |
| **Trazas** | Tempo (Grafana) | Jaeger, Zipkin | OTel-native, integración directa con Grafana, < 256MB RAM |
| **Logs** | Loki (Grafana) | ELK Stack | Ver ADR-0001: reemplazo de ELK por licencias SSPL |
| **Métricas** | Prometheus / Mimir | InfluxDB, TimescaleDB | Estándar de facto CNCF para métricas de infra |
| **Dashboard** | Grafana + React static | Datadog, New Relic | Single pane of glass para logs, trazas y métricas |
| **Alertas** | Grafana Alertmanager | PagerDuty, OpsGenie | Routing multicanal (Mail, Telegram, WhatsApp) |
| **Buffer** | SQLite (WAL mode) | Redis, Kafka | Zero config, zero RAM adicional, suficiente para MVP |
| **Storage** | SQLite + time-index | TimescaleDB (inicial) | Migrable transparente, sin PostgreSQL dedicado |
| **ML** | scikit-learn (Isolation Forest) | PyTorch LSTM (inicial) | < 50MB RAM, CPU-only, suficiente para detección básica |
| **GenIA** | Llama 3.2 1B (llama.cpp) | Llama 3.1 8B, GPT-4 API | 600MB RAM, 5-10 tok/s CPU, sin costo de API |
| **RAG** | sentence-transformers + Chroma | OpenAI embeddings | Local, sin llamadas externas, privacidad garantizada |
| **Self-Monitoring** | Netdata | Prometheus + Grafana | < 5% CPU, 150MB RAM, auto-discovery, per-second |
| **Backup** | Rclone + S3 free-tier | rsync manual | Automático, incremental, 5GB gratis |
| **CI/CD** | GitHub Actions | GitLab CI, Jenkins | Free para repos públicos, integración nativa |
| **Containers** | Docker Compose | Kubernetes | Single-node, setup < 30 min, sin orquestación compleja |

---

## 9. Estrategia de Recursos: 4 Tiers

| Tier | Recurso | Estrategia | Costo |
|------|---------|-----------|-------|
| **Tier 0: On-Premise** | Servidores GIDAS existentes (4-8GB RAM, 2-4 cores) | Maximize reuse: ingest, storage, dashboard, GenIA | $0 |
| **Tier 1: Free-Tier Cloud** | AWS (750h EC2 t2.micro, 5GB S3), GCP (1 f1-micro, 5GB storage) | Burst + backup: DR, alertas, demo público | $0 |
| **Tier 2: Edge** | Raspberry Pi 4 (4GB), Pi Zero 2W | Compute at edge: agentes distribuidos, inference local | ~$35-75/unidad |
| **Tier 3: Shared** | Cluster compartido UTN, horarios no-pico | Time-slicing: entrenamiento ML batch, procesamiento pesado | $0 |

**Footprint total del sistema**: < 2GB RAM | < 2 cores | < 10GB disk (sin datos) | Costo operativo: **$0/mes**

---

## 10. Roadmap Redefinido (24 semanas)

| Fase | Semanas | Metodología | Entregables | SDD | DevOps |
|------|---------|-------------|-------------|-----|--------|
| **FASE 0: Discovery** | 1-2 | Design Sprint | PRD, 4 personas, OpenAPI draft, AsyncAPI draft | Spec-First | — |
| **FASE 1: Anchor** | 3-6 | Scrum (2-sem sprints) | MVP-0: Agente + ingesta + SQLite + FastAPI stubs | Spec-Anchored | CI/CD básico |
| **FASE 2: Build** | 7-14 | Kanban + CI/CD | MVP-1: ML + Dashboard 3 vistas + GenIA + Alertas | Spec-Anchored | Tests + Deploy auto |
| **FASE 3: Validate** | 15-18 | Lean UX + TDD | MVP-2: SUS testing, A/B, benchmarks, security audit | Spec-Anchored | Contract testing |
| **FASE 4: Publish** | 19-24 | Academic Writing | Paper IEEE/ACM, extensión UTN, comunidad | Spec-as-Source | Release semántico |

---

## 11. Stakeholders y Comunicación

| Rol | Institución | Interés | Frecuencia de contacto |
|-----|------------|---------|------------------------|
| Director GIDAS | UTN-FRLP | Liderazgo científico, publicaciones | Semanal |
| Equipo InfraIT | GIDAS | Desarrollo técnico, operación | Diario (standup) |
| SREs Estudiantes | UTN-FRLP | Usuarios finales, feedback UX | Quincenal (demo) |
| Docentes/Investigadores | UTN-FRLP | Datos para papers, reproducibilidad | Mensual |
| Coordinación Extensión | UTN-FRLP | Transferencia tecnológica | Mensual |
| Comunidad Open Source | Global | Adopción, contribuciones | Continuo (GitHub) |

---

## 12. Gestión de Riesgos Redefinida

| Riesgo | Prob. | Impacto | Mitigación |
|--------|-------|---------|------------|
| SQLite no escala para > 10K métricas/seg | Media | Alto | Diseño migrable a TimescaleDB; threshold de 1K/seg en MVP |
| LLM 1B no suficiente para RCA complejo | Media | Medio | Fallback a templates pre-definidos; mejora con fine-tuning futuro |
| Hardware legacy falla durante desarrollo | Baja | Alto | Backup diario a S3 free-tier; Docker Compose para rebuild rápido |
| Baja adopción por falta de GPU/ML "sexy" | Baja | Medio | Comunicar valor de "funciona en cualquier hardware"; demos en vivo |
| Free-tier cloud expira (12 meses AWS) | Media | Medio | Migración a GCP/Azure free-tier; eventual self-hosted completo |
| Complejidad de AsyncAPI para equipo | Baja | Medio | Capacitación interna; empezar con OpenAPI simple |

---

## 13. Presupuesto Redefinido (24 semanas)

| Ítem | Costo Estimado (USD) | Notas |
|------|---------------------|-------|
| Hardware adicional (Pi 4 x 2) | $140 | Para edge agents y testing |
| GPU para entrenamiento futuro | $0 | Usar shared compute UTN o Google Colab free |
| Cloud (free-tier, dentro de límites) | $0 | AWS 12 meses + GCP perpetuo free tier |
| Publicación científica | $500 | IEEE/ACM conference fees |
| Dominio + hosting demo | $50 | GitHub Pages (free) + dominio custom opcional |
| Capacitación equipo (cursos online) | $0 | Free tiers: Coursera audit, AWS training |
| **Total** | **~$690** | **Reducción 79% vs v1.0 ($3,300)** |

---

## 14. KPIs Redefinidos

### 14.1 Técnicos

| KPI | Target | Métrica |
|-----|--------|---------|
| Footprint total | < 2GB RAM | `docker stats` |
| Setup time | < 30 min | Cronometrado en máquina limpia |
| Throughput ingest | > 1K métricas/seg | k6 benchmark |
| Latencia detección | < 5 segundos | Timestamp diff |
| Precision ML | > 80% | TP / (TP + FP) |
| Recall ML | > 75% | TP / (TP + FN) |
| Dashboard load | < 2 segundos | Lighthouse |
| GenIA inference | 5-10 tok/s | llama.cpp benchmark |

### 14.2 De Usuario

| KPI | Target | Métrica |
|-----|--------|---------|
| SUS (System Usability Scale) | > 75 | Cuestionario post-test |
| Time-to-Anomaly | < 10 segundos | Tarea medida |
| Satisfacción GenIA | > 4.0/5 | CSAT post-interacción |
| Mobile usage | > 40% | Analytics del dashboard |

### 14.3 De Investigación

| KPI | Target | Métrica |
|-----|--------|---------|
| Paper científico | 1 submission | IEEE/ACM/SREcon |
| Reproducibilidad | Setup < 30 min | `docker compose up` |
| Transferencia | 2+ laboratorios pilotos | Acuerdos firmados |
| Comunidad | 50+ stars GitHub | Métricas de repo |

---

## 15. Diagramas Generados

1. **[Arquitectura para Recursos Escasos](sandbox:///mnt/agents/output/intellops_resource_constrained_architecture.png)** — Matriz de decisiones de recursos, arquitectura reducida monolito modular, personas UX y roadmap SDD+Agile+DevOps+OpenSpec
2. **[Nicho y Estado del Arte](sandbox:///mnt/agents/output/intellops_nicho_estadoarte.png)** — Mapa de posicionamiento de productos, investigación activa, estándares de industria, atributos de calidad comparativos y características del producto redefinidas

---

## 16. Referencias Clave



- **Observability Platforms 2026**: Comparativa de Datadog, Grafana, New Relic, Signoz, Netdata — arquitectura, costos y data residency 
- **Edge Observability with Netdata**: ML en edge con <5% CPU, 150MB RAM, autonomous operation 
- **AsyncAPI Standard**: Especificación industry-standard para event-driven APIs, equivalente a OpenAPI para REST 
- **Lightweight Kubernetes for Edge**: Raspberry Pi 4B clusters con MicroK8s/K3s, validados en investigación de campo 
- **OpenTelemetry for Edge**: Configuración de OTel Collector para dispositivos con recursos limitados 
- **Spec-First API Development**: Best practices para desarrollo contract-first con OpenAPI 
- **Open Source Observability 2026**: Top 10 plataformas open-source — Parseable, Grafana LGTM, Signoz, OpenObserve, Netdata 

---

**Documento controlado v2.0.**  
*Este brief es un documento vivo. Las modificaciones se versionan en `/docs/project-brief.md` del repositorio del proyecto bajo semantic versioning.*

---