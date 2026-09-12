# IntellOps — Roadmap Completo del Producto (2026–2030)

**Documento**: `roadmap/roadmap-producto.md`
**Fecha**: 2026-09-11
**Autor**: Coordinación InfraIT — Emanuel Rodríguez
**Alcance**: visión completa del producto IntellOps, alineada al PID TC GIDAS (2027–2030) y a las PPS 2026.
**Stack del MVP (ADR-0002)**: React+TS · FastAPI · SQLModel · PostgreSQL · Docker/Podman · VM Rocky 10.

---

## 1. Resumen de Fases

| Fase | Período | Foco | Hito de salida | Alineación PID |
|---|---|---|---|---|
| **F0 — Fundación** | 06–12/2026 | PPS 2026 de los 3 contributors; cimientos técnicos | MVP-0 operativo en laboratorio GIDAS | Antesala E1 |
| **F1 — MVP** | 01–06/2027 | Producto mínimo viable con valor UX | MVP-1 validado (SUS > 75) | E1 (estado del arte) |
| **F2 — Experimentación** | 07/2027–12/2028 | Experimentos IA, correlación m/l/t, prototipo inicial | Prototipo inicial implementado en GIDAS | E1 + E2 |
| **F3 — Prototipo escalable** | 01–12/2029 | Escalabilidad, impacto, transferencia | Plataforma validada + 2 laboratorios adoptantes | E3 |
| **F4 — Cierre y comunidad** | 2029–03/2030 | Publicaciones, PI, comunidad open-source | Informe final + release estable Apache-2.0 | E3 (cierre) |

---

## 2. Fase 0 — Fundación (2026)

### 2.1. Objetivo
Convertir la investigación previa (brief-v2, marco, papers) en **cimientos técnicos ejecutables**, con las PPS 2026 como motor de desarrollo.

### 2.2. Entregables
| # | Entregable | Owner | Dependencia |
|---|---|---|---|
| F0-1 | ADR-0001 (GLP) + ADR-0002 (PostgreSQL) aprobados | Coordinación | — |
| F0-2 | Backlog priorizado E01-E12 + planning poker | Coordinación + equipo | F0-3 |
| F0-3 | Contratos de datos publicados (OpenAPI 3.1 + AsyncAPI 3.0) | Federico/Romeo/Santiago | — |
| F0-4 | M-SEG: hardening CIS + pipeline GLP seguridad + dashboards | Federico | ADR-0001 |
| F0-5 | M-ML: anomalías (IF+zscore) + health score + endpoint | Romeo | F0-3 |
| F0-6 | M-QA: pipeline GitHub Actions + gates + tests | Santiago | F0-3 |
| F0-7 | M-DASH: dashboard React+TS 3 vistas (parcial) | Romeo + Ema | F0-5 |
| F0-8 | M-ING: ingesta FastAPI + PostgreSQL (SQLModel/Alembic) | Coordinación | ADR-0002 |
| F0-9 | Infra: VM Rocky 10, Docker/Podman, compose | Coordinación | — |
| F0-10 | MVP-0 instalado y funcional (lab GIDAS) | Equipo completo | F0-4..F0-9 |

### 2.3. Indicador de éxito
CI verda en todos los PR · coverage ≥ 70% · demo end-to-end (RUM → PostgreSQL → dashboard).

---

## 3. Fase 1 — MVP (01–06/2027)

### 3.1. Objetivo
Evolucionar MVP-0 → **MVP-1**: producto cerrado, validado y documentado para uso interno y extensión.

### 3.2. Entregables
| # | Entregable | Owner | Dependencia |
|---|---|---|---|
| F1-1 | E02/E04/E05/E09 completas (RUM productivo, ML, dashboard 3 vistas, tests) | Team | F0 |
| F1-2 | E06 alertas multicanal (severidad → canal) | Coordinación | E04 |
| F1-3 | Validación SUS con las 4 personas académicas (n=10) | Coordinación | E05 |
| F1-4 | Paper base por módulo (seguridad GLP, ML+health, QA+OTel) | F/R/S | F1-1 |
| F1-5 | Time-to-anomaly < 10s · detección < 5s · ingesta ≤ 500ms · F1 ≥ 0.70 | Team | F1-1 |

### 3.3. Hito
**MVP-1 validado**: cumple los criterios de aceptación del sistema (`04-especificaciones.md` §6) y es presentable a dirección GIDAS.

---

## 4. Fase 2 — Experimentación y Prototipo Inicial (07/2027–12/2028)

### 4.1. Objetivo
Alinear el producto con el plano de experimentación del PID: estado del arte, metodología, experimentos IA sobre la infra GIDAS, e **implementación inicial del prototipo** (nov 2028).

### 4.2. Entregables
| # | Entregable | Alineación PID | Período |
|---|---|---|---|
| F2-1 | Estado del arte actualizado (observabilidad + AIOps + IA en software) | E1 (04/2027–08/2027) | 07–08/2027 |
| F2-2 | Exploración de herramientas (OTel, Prometheus, Grafana, Postgres/TimescaleDB) | E1 (07–10/2027) | 07–10/2027 |
| F2-3 | Diseño metodológico de experimentos (protocoles, métricas, control) | E1 (09–11/2027) | 09–11/2027 |
| F2-4 | Ensayos exploratorios integrados con infra GIDAS | E1 (10/2027–01/2028) | 10/2027–01/2028 |
| F2-5 | Experimentos IA sobre infra GIDAS (anomalías, health score, forecast) | E2 (02–05/2028) | 02–05/2028 |
| F2-6 | Validación de técnicas + ajuste de procesos | E2 (05–07/2028) | 05–07/2028 |
| F2-7 | Pruebas de integración y correlación métricas/logs/trazas | E2 (08–11/2028) | 08–11/2028 |
| F2-8 | Evaluación de impacto en performance y UX (infra GIDAS) | E2 (10–12/2028) | 10–12/2028 |
| F2-9 | **Implementación inicial del prototipo** (mejora calidad servicios IT) | E2 (11/2028–02/2029) | 11/2028–02/2029 |

### 4.3. Hito
**Prototipo inicial documentado**: metodología reproducible (DVC/MLflow), datos exportables, resultados de experimentos en repo.

---

## 5. Fase 3 — Prototipo Escalable y Transferencia (2029)

### 5.1. Objetivo
Consolidar el prototipo → **plataforma escalable**, validar impacto y transferir a adoptantes externos.

### 5.2. Entregables
| # | Entregable | Alineación PID | Período |
|---|---|---|---|
| F3-1 | Puesta a punto y pruebas de escalabilidad del prototipo | E3 (02–05/2029) | 02–05/2029 |
| F3-2 | Evaluación de impacto tecnológico + documentación de metodologías | E3 (05–07/2029) | 05–07/2029 |
| F3-3 | Transferencia ampliada (empresas, pymes, organismos, UTN) | E3 (07–10/2029) | 07–10/2029 |
| F3-4 | Artículos científicos + propiedad intelectual | E3 (09–12/2029) | 09–12/2029 |
| F3-5 | Talleres de formación RRHH + informe final del PID | E3 (11/2029–03/2030) | 11/2029–03/2030 |

### 5.3. Hito
**Plataforma validada en 2+ laboratorios adoptantes** con evidencia de impacto (MTTR, incidentes evitados, UX).

---

## 6. Fase 4 — Cierre y Comunidad (2029–03/2030)

### 6.1. Entregables
| # | Entregable | Detalle |
|---|---|---|
| F4-1 | Informe final del PID | Resultados, metodologías, transferencia |
| F4-2 | Release estable Apache-2.0 | Tag semántico, SBOM, changelog, onboarding renovado |
| F4-3 | Comunidad open-source activa | Issues/triado, contribuciones externas, docs vivas |
| F4-4 | Sostenibilidad post-proyecto | Plan de mantenimiento, governance, roadmap post-PID |

### 6.2. Hito
**Cierre formal del PID TC** (31/03/2030) con todos los entregables de E3 completos.

---

## 7. Dependencias Cruzadas Producto ↔ PID

| IntellOps (Fase/Roadmap) | PID E1/E2/E3 | Naturaleza |
|---|---|---|
| F1 (MVP) | E1 (estado del arte) | IntellOps aporta evidencia técnica del estado del arte |
| F2-4..F2-9 | E1→E2 | Los experimentos IntellOps **son** los experimentos del PID |
| F3 | E3 | El prototipo IntellOps **es** el prototipo del PID |
| F4 | E3 (cierre) | Los papers de IntellOps alimentan los artículos del PID |

**Principio**: IntellOps es la materialización de producto del PID; el roadmap del PID y el del producto
NO divergen (mismo equipo, misma infra, mismas entregas).

---

## 8. Vectores de Costo (todas las fases)

| Concepto | Costo |
|---|---|
| Software / licencias | $0 (todo open-source, Apache-2.0/AGPL en infraestructura as-is) |
| Cloud | $0 free-tier (AWS 12m + GCP perpetuo) o VM existente |
| Hardware | Ya disponible (VM Rocky 10; servidores legacy GIDAS) |
| Publicaciones | ~$500 (fees de conferencia, dentro del presupuesto del PID) |

---

## 9. KPIs por Fase

| KPI | F0 | F1 | F2 | F3 | F4 |
|---|---|---|---|---|---|
| Coverage | ≥ 70% | ≥ 70% | ≥ 70% | ≥ 75% | ≥ 75% |
| F1 (anomalías) | — | ≥ 0.70 | ≥ 0.75 | ≥ 0.80 | ≥ 0.80 |
| Time-to-anomaly | — | < 10s | < 8s | < 8s | < 8s |
| SUS | — | > 75 | > 75 | > 78 | > 78 |
| Uptime stack | > 99% | > 99.5% | > 99.5% | > 99.5% | > 99.5% |
| Costo mensual | $0 | $0 | $0 | $0 | $0 |
| Laboratorios adoptantes | 0 | 0 | 0 | 2+ | 2+ |
| Publicaciones | 0 | 3 borradores | 2 papers | 2+ papers | 4+ publicaciones |

---

## 10. Riesgos del Roadmap

| Riesgo | Fase | Mitigación |
|---|---|---|
| PPS terminan (oct 2026) sin entregables completos | F0 | Contratos publicados temprano; seguimiento semanal; DoD único |
| Resultados de experimentos no cumplen F1 objetivo | F2 | Baselines livianos primero (IF/zscore); LSTM como extensión; datasets versionados |
| VM queda corta en RAM (PostgreSQL sumado al stack) | F0/F1 | Tuning conservador; Netdata; presupuesto de recursos por contenedor |
| Adopción externa lenta | F3 | Convenios por dirección GIDAS; demo pública read-only; documentación de deploy < 30 min |
| Free-tier cloud expira (AWS 12 meses) | F1+ | GCP perpetuo + self-hosted completo en VM |
| Cambios de stack posteriores (post-PID) | F4 | ADRs vivos; repositorios con interfaz; especificaciones versionadas |

---

*Documento vivo — se actualiza en cada hito de fase y en el sprint review del backlog.*