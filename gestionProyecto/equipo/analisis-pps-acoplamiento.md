# PPS 2026 — Verificación de Planes y Acoplamiento al Marco IntellOps

**Documento**: `../equipo/analisis-pps-acoplamiento.md`
**Fecha**: 2026-09-11
**Autor**: Coordinación InfraIT — Emanuel Rodríguez
**Objetivo**: verificar que los planes de trabajo PPS de los colaboradores sean coherentes, cohesivos y
alineados al marco conceptual de IntellOps (`../marco/01-objetivo.md` → `04-especificaciones.md`),
y proponer los cambios concretos para lograrlo.

**Fuentes verificadas**:
- `RRHH/Federico Cavallero/PPS2_PlanTrabajo_IntellOps_Blanco_Cavallero_v2.docx`
- `RRHH/Federico Cavallero/Cronograma_IntellOps_Blanco_Cavallero_v3.*`
- `RRHH/Romeo Monfroglio/PPS2_PlanTrabajo_IntellOps_V06_2026.docx`
- `RRHH/Romeo Monfroglio/Plan de trabajo y cronograma.pdf`
- `RRHH/Santiago Montanari/PPS2_PlanTrabajo_IntellOps_Montanari_v2.docx`
- `RRHH/Santiago Montanari/Cronograma_IntellOps_Montanari_v2.docx`
- `PID/Nahuel - Proyecto.pdf` (marco institucional)
- `../marco/*`, `docs/brief-v2.md`, `docs/adr/0001-*.md`, `TEAM_CHARTER.md`, `governance/plan-trabajo.md`

---

## 1. Resumen Ejecutivo de Verificación

| Colaborador | Módulo PPS actual | Coherencia con marco | Hallazgos |
|---|---|---|---|
| **Federico Blanco Cavallero** | Seguridad (hardening CIS + pipeline logs + dashboards) | 🟡 Parcial | Versión v2 usa **ELK Stack**, contradice ADR-0001 (GLP); su propio cronograma v3 ya migró a Grafana. Necesita unificar a GLP y conectar con la capa RUM. |
| **Romeo Lorenzón Monfroglio** | Observabilidad + Detección de Anomalías (ML) | 🟢 Alta | Bien alineado a IO3/IO4; ya menciona agente RUM/UX. Pendiente: formalizar health score y RCA en el plan; el plan PDF difiere del DOCX. |
| **Santiago Montanari** | QA (testing + CI/CD + métricas de calidad) | 🟢 Alta | Bien alineado; transversal por naturaleza. Pendiente: incluir explícitamente quality gates OTel (synthetic journeys) y validación de UX. |

**Diagnóstico general**: los tres planes **aportan piezas correctas** pero **no hablan el mismo idioma
arquitectónico**. Faltan: (1) un lenguaje común de capas (UX → Producto → Infra), (2) contratos de datos
compartidos, (3) DoD único derivado de las especificaciones del marco, (4) interlocking explícito entre
módulos (quién consume qué de quién).

---

## 2. Marco de Referencia para el Acoplamiento

Del manual `../marco/03-diseno.md` §4, cada PPS debe mapear a un módulo con **fronteras
explícitas** y **contratos de interfaz**:

```
Módulo (PPS)          Entrega funcional              Interfaz consumida/producida
─────────────────────────────────────────────────────────────────────────────────────
FEDERICO  · M-SEG     Seguridad: hardening CIS +      Produce: logs de seguridad (GLP),
                      pipeline GLP + dashboards        eventos auth/ssh; dashboards JSON.
                                                       Consume: specs de ingesta (API).
ROMEO    · M-ML       Detección de anomalías +        Produce: anomaly_list, health_score,
           + M-RCA    forecast + RCA asistido por      RCA text, modelos versionados.
                      LLM local + RAG                  Consume: métricas RUM + infra
                                                       (PostgreSQL/GLP), trazas Tempo.
SANTIAGO · M-QA       Tests + CI/CD + quality gates   Produce: pipeline, reportes de
           + M-DASH?  + synthetic journeys OTel        cobertura, gates OTel, informe
                                                       de rendimiento. Consume: API,
                                                       contratos OpenAPI/AsyncAPI.
```

**Regla de acoplamiento**: cada PPS *produce* artefactos consumibles por otro PPS. Si un plan no define
qué produce y qué consume, no está acoplado.

---

## 3. Verificación Individual y Propuestas de Cambio

### 3.1. Federico Blanco Cavallero — Módulo de Seguridad (200 hs, 01/06 → 19/10/2026)

#### 3.1.1. Qué tiene su plan (verificado)
- A1 (30hs): Auditoría inicial Lynis/OpenSCAP + benchmark ELK/Wazuh/Graylog
- A2 (25hs): Diseño arquitectónico + ADRs
- A3 (35hs): Hardening CIS Level 1 con Ansible (Lynis ≥ 70%)
- A4 (55hs): Pipeline ELK (Filebeat/Auditbeat → Logstash → Elasticsearch)
- A5 (40hs): Dashboards Kibana + alertas
- A6 (10hs): Testing E2E + integración con IntellOps
- A7 (5hs): Informe final + paper

#### 3.1.2. Hallazgos

| # | Hallazgo | Severidad | Evidencia |
|---|---|---|---|
| H-F1 | **El plan de trabajo v2 dice ELK Stack, pero el ADR-0001 del proyecto ya decidió Grafana + Loki + Prometheus (GLP)** por licencia SSPL de Elastic. Su propio *Cronograma v3* ya está titulado "GRAFANA Stack + Dashboards GRAFANA". Hay contradicción interna entre v2 y v3. | 🔴 Alta | `docs/adr/0001` vs `PPS2_PlanTrabajo_v2` vs `Cronograma_v3` |
| H-F2 | El cronograma v3 (PDF) no está acompañado de una actualización del PPS2 (Plan de Trabajo oficial). La PPS se evalúa sobre el PPS2. | 🟠 Media | Solo `.docx` de plan v2; el v3 es cronograma |
| H-F3 | El benchmark (A1) compara ELK/Wazuh/Graylog — no evalúa GLP/GLP-Stack siendo GLP la decisión del proyecto. Rehacer benchmark contra GLP. | 🟠 Media | A1 contenido |
| H-F4 | No explicita **contrato de datos** con el resto del sistema: formato de eventos de seguridad, índice/etiquetas en Loki, dashboard JSON versionado. | 🟠 Media | Secciones 5-7 del plan |
| H-F5 | El objetivo general no menciona **experiencia de usuario** ni cómo la seguridad impacta en confiabilidad del producto — desalineación con el objetivo macro IO6. | 🟡 Baja | Objetivo general del plan |

#### 3.1.3. Cambios propuestos

1. **Unificar el stack**: reemplazar en PPS2 todo el texto "ELK Stack / Elasticsearch / Logstash / Kibana" por **"GLP (Grafana + Loki + Prometheus) + Promtail", citando ADR-0001** (y la variante: componente de almacenamiento puede ser Grafana Loki con retención configurada). Actualizar título: *"Hardening CIS + GLP (Grafana/Loki/Prometheus)"*.
2. **Actualizar el PPS2 a v3** en formato oficial (no solo cronograma): llevar A4 a "Pipeline GLP de seguridad (Promtail → Loki; dashboards Grafana)" y A5 a "Dashboards Grafana + alertas de seguridad".
3. **Redefinir A1**: benchmark de herramientas de seguridad sobre **GLP** (auditbeat/promtail con Loki, Falco, Wazuh) manteniendo la justificación de licencias del ADR-0001.
4. **Añadir contrato de datos** (entregable explícito): schema de eventos de seguridad (`auth.success`, `auth.failed`, `config.change`, `process.exec`) con etiquetas Loki estandarizadas, para que Romeo/Santiago consuman.
5. **Vincular a IO6/IO5**: en la fundamentación, explicar que el módulo de seguridad soporta la confiabilidad del producto que ve el usuario (objetivo del PID OE4 + IO6).

**Resultado**: M-SEG entrega un módulo de seguridad GLP, integrado al repositorio, con dashboards
importables, contrato de datos publicado, y documentación publicable (Lynis antes/después).

---

### 3.2. Romeo Lorenzón Monfroglio — Observabilidad + Detección de Anomalías (200 hs, 04/05 → 18/09/2026)

#### 3.2.1. Qué tiene su plan (verificado — DOCX V06 y PDF difieren)
- A1 (30hs): Análisis de caso de negocio + benchmark (Grafana, Datadog, New Relic, Prometheus)
- A2 (25hs): Diseño arquitectónico + selección de stack (FastAPI/Golang, TimescaleDB, React/Angular)
- A3 (40hs): Agente de captura (JS/browser) + backend de ingesta + TimescaleDB
- A4 (50hs): Modelos ML (LSTM, Isolation Forest, Prophet) + pipeline
- A5 (35hs): Dashboard interactivo (3 vistas: latencias, heatmap, predicciones)
- A6 (10hs): Testing/validación con datos reales
- A7 (10hs): Informe final

#### 3.2.2. Hallazgos

| # | Hallazgo | Severidad | Evidencia |
|---|---|---|---|
| H-R1 | **El plano DOCX del proyecto IntellOps ha evolucionado (ver `docs/research/rum-observability`, brief-v2, ADR-0002): la base de datos del MVP es PostgreSQL + SQLModel (ADR-0002, 2026-09-11), NO TimescaleDB directo ni SQLite.** El plan debe alinearse al ADR-0002. | 🟠 Media | Plan A3 vs ADR-0002 |
| H-R2 | Modelos: LSTM+IF+Prophet de golpe; el marco/brief exige **baseline liviano (IF + z-score + seasonal) primero, LSTM como extensión** por recursos. | 🟠 Media | Plan A4 vs brief-v2 §4.3 |
| H-R3 | El gran aporte del marco — **User Health Score** y **clasificador de reclamos / RCA** (IO4) — no está en el plan V06; sí aparece en `governance/plan-trabajo.md` como Fase 2. | 🟠 Media | Plan vs governance |
| H-R4 | El PDF "Plan de trabajo y cronograma" difiere del DOCX V06 (contenido), creando ambigüedad de cuál es la versión vigente. | 🟠 Media | Archivos duplicados incompatibles |
| H-R5 | No explicita el contrato de consumo: qué métricas consume (RUM de Federico/agente, trazas Tempo) para detectar anomalías. | 🟡 Baja | Plan |

#### 3.2.3. Cambios propuestos

1. **Alinear storage**: cambiar A3 a "PostgreSQL + SQLModel + Alembic (migraciones), con TimescaleDB como extensión futura" citando ADR-0002. Nota: esta recomendación reemplaza a la alineación previa a SQLite (el contexto de recursos cambió: VM Rocky 10 dedicada).
2. **Alinear ML**: A4 → "Baseline: Isolation Forest + Z-score + seasonal decomposition (CPU, <50MB). LSTM/Prophet documentados como experimento de extensión (si recursos lo permiten)".
3. **Incorporar IO4 al plan**: agregar A4.5 (~15-20hs): **definir e implementar User Health Score (0-100, pesos configurables, endpoint `GET /ml/health-score/:userId`)** como aporte central de valor diferencial; y A4.6: **clasificador predictivo de reclamos** (si el tiempo lo permite, F1 ≥ 0.75).
4. **RCA asistido por LLM**: documentar en A5 como extensión (M-RCA) que consume trazas Tempo + logs Loki; no comprometer en el MVP si el foco es detección/health score.
5. **Unificar versión**: definir el DOCX V06 como vigente y regenerar el PDF con el mismo contenido (o eliminar el PDF viejo).
6. **Definir contrato de consumo**: métricas de entrada (schemas RUM/metrics de ingesta), salida (payload `AnomalyList` con `capa`, `impacto_ux_estimado`, consumible por alertas del dashboard).

**Resultado**: M-ML entrega detección de anomalías + health score funcionales sobre datos reales,
consumiendo la telemetría de las capas UX/Producto/Infra, con endpoints API utilizables por M-QA y M-DASH.

---

### 3.3. Santiago Montanari — QA / CI-CD (200 hs, 01/06 → 19/10/2026)

#### 3.3.1. Qué tiene su plan (verificado)
- A1 (30hs): Análisis de calidad actual + benchmark herramientas QA
- A2 (25hs): Diseño de estrategia de testing + ADRs
- A3 (35hs): Pipeline CI/CD GitLab + Docker Compose testing
- A4 (55hs): Suite unitarias + integración API REST (coverage ≥ 70%)
- A5 (40hs): E2E + rendimiento/carga (ingesta ≤ 500ms)
- A6 (10hs): Calibración quality gates + validación equipo
- A7 (5hs): Informe final + paper

#### 3.3.2. Hallazgos

| # | Hallazgo | Severidad | Evidencia |
|---|---|---|---|
| H-S1 | El plan habla de **GitLab CI/CD**, pero el repositorio actual usa **GitHub Actions** (`.github/workflows/ci.yml`). Desalineación de herramienta. | 🟠 Media | Plan A3 vs `.github/` |
| H-S2 | No incluye **synthetic user journeys instrumentados OTel** ni **quality gates basados en señales OTel** (latencia p99, error rate) — que es exactamente el aporte diferencial "Observability-Driven QA" del `governance/plan-trabajo.md` Fase 2. | 🟡 Baja-Media | Plan vs governance T2.1/T2.2 |
| H-S3 | E2E (A5) no menciona validar **trazas completas en Tempo** (frontend→backend) ni correlación con health score. | 🟡 Baja | Plan A5 |
| H-S4 | No explicita cómo su módulo *consume* los contratos OpenAPI/AsyncAPI (contract testing con schemathesis mencionado en governance, no en PPS2). | 🟡 Baja | Plan |

#### 3.3.3. Cambios propuestos

1. **Alinear herramienta**: A3 → "Pipeline **GitHub Actions** (CI existente en `.github/workflows/ci.yml`): lint → unit → integration-test → contract → build → deploy-staging" (GitLab solo si la Coordinación PPS lo exige; en ese caso, justificar duplicación).
2. **Incorporar Observability-Driven QA**: agregar A5.5 (~15hs): **synthetic journeys OTel** (login+consulta, carga dashboard, reporte de error) que generen trazas validadas en Tempo y alimenten gates de latencia p99 < 200ms / error rate < 0.1%.
3. **Ampliar E2E a UX**: A5 validar además: "las 3 vistas del dashboard cargan en < 2s; una anomalía simulada llega al canal de alertas < 30s".
4. **Añadir contract testing**: A4 incluir "contract testing con schemathesis contra OpenAPI spec (≥ 80% endpoints)" y validación AsyncAPI.
5. **Vincular a IO6**: en fundamentación, QA es el habilitante transversal: garantiza que los módulos de Federico y Romeo se integren sin regresiones (cita RF-QA-02..05).

**Resultado**: M-QA entrega una pipeline GitHub Actions real con gates de calidad y de telemetría,
suites de tests (unit/integration/E2E/contract), y evidencia de rendimiento — el seguro del sistema completo.

---

## 4. Acoplamiento: Matriz de Interdependencias Entre PPS

Las entregas de cada PPS deben **encajar** (interlocking). Matriz propuesta:

```
                    PRODUCE ──►                        CONSUME ◄──
FEDERICO (M-SEG) ──► logs de seguridad (Loki),
                     dashboards GLP seg,               ◄── métricas de API (para correlacionar
                     eventos auth/ssh                   │     seguridad↔rendimiento)
        │                                              │
        ▼                                              ▼
ROMEO (M-ML)     ──► anomaly_list, health_score,      ◄── métricas RUM (Federico/Ema),
                     forecast, RCA text                 │   trazas Tempo, logs Loki (Santiago
        │                                              │   valida calidad de datos)
        ▼                                              ▼
SANTIAGO (M-QA)   ──► pipeline CI/CD, gates,           ◄── OpenAPI/AsyncAPI specs,
                     reportes cobertura/rendimiento,    │   APIs de todos los módulos,
                     synthetic journeys                 │   health score (Romeo) para gates
```

**Implicancias operativas del acoplamiento**:
1. **Orden de integración**: M-SEG (infra/seguridad) y M-ML (core) primero; M-QA acompaña desde el día 1 (aunque QA "no tiene dependencias" en el plan, en la práctica necesita specs para contract testing).
2. **Contratos publicados temprano**: cada módulo publica su contrato (OpenAPI/AsyncAPI + schema de datos) **antes** de implementar, para que los demás desarrollen contra el contrato.
3. **DoD único** (del marco §04-06): todos usan los mismos criterios — coverage ≥ 70%, spec validada, ADR si aplica, insumo publicable, integración limpia con CI.
4. **Revisión cruzada quincenal**: cada colaborador revisa el PR del otro (peer review) para reforzar el acoplamiento — ya está en TEAM_CHARTER.

---

## 5. Plan de Acción para la Coordinación

| # | Acción | Responsable | Plazo sugerido |
|---|---|---|---|
| 1 | Aprobar marco conceptual `../marco/01-04` (revisión del equipo) | Ema + equipo | 1 semana |
| 2 | Solicitar a Federico la **v3 del PPS2** con GLP (cambios §3.1.3) | Ema | 1 semana |
| 3 | Solicitar a Romeo **unificación de versión DOCX/PDF + cambios §3.2.3** | Ema | 1 semana |
| 4 | Solicitar a Santiago **cambios §3.3.3 (GitHub Actions + gates OTel)** | Ema | 1 semana |
| 5 | Definir **contratos de datos compartidos** (eventos de seguridad, payload anomalías, health score) | Ema con los 3 | 2 semanas |
| 6 | Refinar backlog `../backlog/backlog.md` con el equipo y estimar | Ema + equipo | 2 semanas |
| 7 | Taller de alineación: presentar marco + diagrama de actividades a los 3 colaboradores | Ema | 2 semanas |

---

## 6. Conclusión

Los tres planes PPS **son recuperables y valiosos**: ninguno está mal enfocado en su núcleo. El problema
no es el contenido, es la **coherencia entre ellos y con la arquitectura del sistema**. Con los cambios
propuestos (unificar stack GLP, alinear storage/ML al brief-v2, sumar health score y QA con telemetría,
y publicar contratos), los tres módulos se convierten en **las tres patas del mismo taburete**:
**seguridad confiable (Federico) + inteligencia predictiva (Romeo) + calidad verificable (Santiago)**,
sosteniendo el objetivo macro: observabilidad predictiva centrada en el usuario como valor diferencial
del PID de GIDAS.

---

*Documento de análisis. Las versiones oficiales de los planes PPS se actualizan por los propios colaboradores con la coordinación de la PPS.*