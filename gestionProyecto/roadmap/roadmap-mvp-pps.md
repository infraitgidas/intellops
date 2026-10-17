# IntellOps — Roadmap del MVP mapeado a las PPS 2026

**Documento**: `roadmap/roadmap-mvp-pps.md`
**Fecha**: 2026-09-11
**Autor**: Coordinación InfraIT — Emanuel Rodríguez
**Propósito**: acotar el roadmap completo (2026–2030) a la ventana del **MVP y de las PPS 2026**
de Federico Blanco Cavallero (Seguridad), Romeo Monfroglio (ML/Anomalías) y Santiago Montanari (QA).
**Stack de referencia (ADR-0002)**: React+TS · FastAPI · SQLModel · PostgreSQL · Docker/Podman · VM Rocky 10.

---

## 1. Alcance del MVP en el marco de las PPS

Las PPS 2026 tienen 3 restricciones duras:
1. **Ventana temporal**: Romeo (04/05 → 18/09/2026) · Federico y Santiago (01/06 → 19/10/2026).
2. **200 horas efectivas por contributor** (10 hs/semana).
3. **Entrega evaluable**: plan de trabajo oficial (PPS2) + informe final.

**Definición operativa del MVP (para las PPS)**: el MVP-0/MVP-1 del backlog (items **Must** de E01/E02/E03/E04/E07/E08/E09, y **Should** E05/E06 cuando el tiempo lo permita) **no son un "mini producto final" sino el conjunto de módulos independientes acoplados entre sí** — de ahí el nombre "MVP" acotado: cada módulo es una entrega completa y unificable.

---

## 2. Mapeo Épicas → Contributors (resumen)

| Épica | Módulo | Prioridad | Owner (PPS) | Ventana |
|---|---|---|---|---|
| E01 Fundaciones | infra | M | X (todos) | jun–jul |
| E02 Captura RUM | M-RUM | M | Federico (Fase 2, si tiempo) | ago–sep |
| E03 Ingesta y Storage | M-ING | M | X (Coordinación + Pablo/QA) | jun–ago |
| E04 ML + Health Score | M-ML | M | Romeo | may–ago |
| E05 Dashboard 3 vistas | M-DASH | S | Romeo + Ema | ago–oct |
| E06 Alertas | M-ACT | S | X | sep–oct |
| E07 Seguridad | M-SEG | M | Federico | jun–oct |
| E08 CI/CD Gates | M-QA | M | Santiago | jun–ago |
| E09 Testing | M-QA | M | Santiago | jul–sep |
| E10 RCA/GenIA | M-RCA | S | Romeo (Fase 2) | oct+ (post-PPS) |
| E11 QA Observability-Driven | M-QA | S | Santiago (Fase 2) | oct+ (post-PPS) |
| E12 Evaluación/Transferencia | — | S | X | oct+ |

**Nota**: E10, E11 y E12 **exceden la ventana de las PPS 2026** (se planifican para F1/F2 del roadmap de producto). El MVP de las PPS cubre: **E01, E02, E03, E04, E05 (parcial), E06 (parcial), E07, E08, E09**.

---

## 3. Timeline del MVP por Contributor

### 3.1. Romeo Monfroglio — M-ML (+ M-RCA post-PPS) · 04/05 → 18/09/2026

| Semana | Entregable | Épica | Detalle clave |
|---|---|---|---|
| may 1–2 | Esqueleto ML Engine (`base.py`, pipeline train/predict/eval) | E04 | EXP-001 seed fijo |
| may 3–4 | Detector Isolation Forest + Z-score + seasonal; ensamble | E04 | F1 ≥ 0.70 objetivo |
| jun 1–2 | Endpoint `POST /ml/detect` → `AnomalyList` | E04 | payload con `capa`, `impacto_ux_estimado` |
| jun 3–4 | **PostgreSQL (ADR-0002)**: repositorios SQLModel + lecturas ML | E03/E04 | adapter a la interfaz de datos |
| jul 1–4 | EDA con datos reales + EXP-001 versionado + `make reproduce` | E04 | DVC/MLflow |
| ago 1–2 | User Health Score 0-100 (pesos configurables) + endpoint | E04 | r > 0.75 con reclamos |
| ago 3–4 | Dashboard vista 3 (predicciones/anomalías) — React+TS | E05 | con Ema |
| sep 1–2 | Informe final PPS + revisión cruzada (PR) | E12 | insumo paper ML |

### 3.2. Federico Blanco Cavallero — M-SEG (+ M-RUM Fase 2) · 01/06 → 19/10/2026

| Semana | Entregable | Épica | Detalle clave |
|---|---|---|---|
| jun 1–2 | Auditoría baseline: Lynis + OpenSCAP + informe | E07 | antes → después documentado |
| jun 3–4 | Hardening CIS Level 1 (playbooks Ansible, staging) | E07 | Lynis ≥ 70% |
| jul 1–2 | Pipeline GLP seguridad: Promtail → Loki; etiquetas estándar | E07 | ADR-0001 ya define GLP |
| jul 3–4 | 4 dashboards Grafana seguridad (JSON versionados) | E07 | auth, brute-force, cambios críticos, alertas |
| ago 1–2 | Contrato de datos de eventos (schema publicado) | E07 | consumible por E04 |
| ago 3–4 | Prueba detección evento simulado (< 60s) | E07 | benchmark GLP (reemplaza ELK) |
| sep 1–2 | Integración con ingesta (validar contra OpenAPI) | E07/E03 | interlocking con Santiago |
| sep 3–4 | Agente RUM productivo (bundle < 30KB) — Fase 2 | E02 | CORS echo origin + OTLP |
| oct 1–2 | Transporte RUM + tests de agente | E02 | si tiempo |

### 3.3. Santiago Montanari — M-QA · 01/06 → 19/10/2026

| Semana | Entregable | Épica | Detalle clave |
|---|---|---|---|
| jun 1–2 | Análisis de calidad actual + benchmark herramientas QA | E08 | — |
| jun 3–4 | Pipeline **GitHub Actions** (lint → unit → integration → contract → build) | E08 | NO GitLab (H-S1) |
| jul 1–2 | Quality gates: coverage < 70% bloquea; lint warnings bloquean | E08 | badges + reporte |
| jul 3–4 | Suite unitaria API (coverage ≥ 70% módulos críticos) | E09 | — |
| ago 1–2 | Tests integración API REST (contratos, bordes, mocks) | E09 | schemathesis ≥ 80% endpoints |
| ago 3–4 | E2E flujo completo: captura → ingesta → PostgreSQL → consulta | E09 | ≥ 3 escenarios |
| sep 1–2 | Pruebas de carga: ingesta ≤ 500ms (k6/Locust) | E09 | reporte |
| sep 3–4 | Calibración de gates + validación equipo | E09/E11 | — |
| oct 1–2 | Synthetic journeys OTel (login, dashboard, reporte error) — Fase 2 | E11 | trazas en Tempo |

---

## 4. Interdependencias (interlocking entre PPS)

```
                    PRODUCE ──►                  CONSUME ◄──
FEDERICO (M-SEG) ──► logs seguridad (Loki),   ◄── métricas API (correlación
                     dashboards GLP, eventos    │  seguridad↔rendimiento)
                     auth/ssh                    │
        │                                       ▼
        ▼                                       │
ROMEO (M-ML)    ──► anomaly_list, health      ◄── métricas RUM + infra
                     score, EXP-001            │  (PostgreSQL/GLP), trazas Tempo
        │                                       ▼
        ▼                                       │
SANTIAGO (M-QA) ──► pipeline CI/CD, gates,    ◄── specs OpenAPI/AsyncAPI,
                     reportes, journeys         │  APIs de todos, health score
```

**Puntos críticos de dependencia**:
1. **Contratos publicados antes de implementar**: el schema de eventos de seguridad (Federico) alimenta
   la detección de Romeo; la OpenAPI/AsyncAPI (Coordinación) alimenta el contract testing de Santiago.
2. **PostgreSQL (ADR-0002) disponible antes de julio**: lo usa Romeo (jun–jul) y el E2E de Santiago (ago).
3. **Health score (Romeo) listo para agosto**: lo consumen los gates de Santiago (E11, Fase 2) como señal.

---

## 5. Secuencia Semanal Consolidada (tablero del MVP)

| Mes | Coordinación | Federico | Romeo | Santiago |
|---|---|---|---|---|
| **May** | ADR-0002, infra VM Rocky 10 | — | fundaciones ML + IF/zscore | — |
| **Jun** | contrato OpenAPI/AsyncAPI | audit Lynis + hardening CIS | ML + endpoint detect | pipeline GA + gates |
| **Jul** | PostgreSQL+SQLModel listo | GLP seguridad + dashboards | EXP-001 + health score | suite unitaria |
| **Ago** | revisión de integración | contrato eventos + RUM prod | dashboard vista 3 + informe | tests integración + E2E |
| **Sep** | plan F1 2027 (MVP-1) | RUM transporte + tests | informe final + paper | carga + gates OTel (F2) |
| **Oct** | cierre PPS + retro | informe final + paper | (post-PPS → E10 RCA) | informe final + paper |

---

## 6. DoD por Módulo (criterios de aceptación — de `04-especificaciones.md`)

| Módulo | DoD verificable |
|---|---|
| M-SEG (Federico) | Lynis ≥ 70% (antes/después) · eventos simulados detectados < 60s · 4 dashboards JSON versionados · contrato de datos publicado |
| M-ML (Romeo) | F1 ≥ 0.70 · health score correlacionado r > 0.75 · EXP-001 reproducible (`make reproduce`) · endpoints documentados |
| M-QA (Santiago) | Pipeline GA verde < 10 min · coverage ≥ 70% · gates bloquean PR · E2E 3 escenarios · informes de carga |
| M-ING (Coordinación) | Ingesta ≥ 1K m/s · PostgreSQL+SQLModel con migraciones Alembic · CORS echo origin + API key |

---

## 7. Riesgos del MVP-PPS

| Riesgo | Prob. | Impacto | Mitigación |
|---|---|---|---|
| Romeo termina PPS en sep sin health score completo | Media | Alta | Health score priorizado antes que dashboard; dashboard parcial OK |
| Federico "Fase 2" (RUM) no entra en ventana | Media | Media | RUM queda en backlog F1 2027; no bloquea integración |
| PostgreSQL no listo para julio | Baja | Alta | Coordinación libera compose con servicio `db` en las primeras semanas |
| Santiago sin specs para contract testing | Media | Media | Contratos publicados en junio (Coordinación) — prioridad #1 |
| 200 hs no alcanzan para todo lo "Must" | Media | Media | Reducir a E01..E09; E05/E06 en modo "resto de tiempo"; documentar ajuste en PPS2 |

---

## 8. Post-MVP (transición a F1 2027)

- **oct–dic 2026**: E05/E06 completas, E10 (RCA/GenIA) y E11 (gates OTel) como extensión de Romeo y Santiago (post-evaluación PPS, si continúan como colaboradores).
- **ene–jun 2027**: MVP-1 completo + validación SUS + papers base → arranque formal del PID E1.

---

*Documento de gestión. El tablero semanal se ajusta en el standup; el horizonte de planificación se revisa cada sprint (2 semanas).*