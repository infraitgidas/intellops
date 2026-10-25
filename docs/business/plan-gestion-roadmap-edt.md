# Plan de Gestión Unificado — Roadmap, EDT e Hitos

Documento único de gestión para IntellOps que reúne el marco estratégico (roadmap F0–F4 de
`gestionProyecto`), la línea operativa (EDT de 8 sprints de `develop`) y el mapeo de los hitos
M0–M4 del plan de la dirección. Resuelve la convivencia de tres líneas base y tres definiciones
de MVP con una correspondencia explícita.

**Alcance:** gestión de proyecto (fases, calendario, dueños, hitos, indicadores y riesgos).
No redefine alcance técnico ni arquitectura.

---

## 1. Marco estratégico: roadmap F0–F4 (2026–2030)

Fuente: `gestionProyecto/roadmap/roadmap-producto.md` (§1), alineado al PID TC GIDAS 2027–2030.

| Fase | Período | Foco | Hito de salida |
|------|---------|------|----------------|
| **F0 — Fundación** | 06–12/2026 | PPS 2026 de los 3 contributors; cimientos técnicos | **MVP-0** operativo en GIDAS |
| **F1 — MVP** | 01–06/2027 | Producto mínimo viable con valor UX | **MVP-1** validado (**SUS > 75**) |
| **F2 — Experimentación** | 07/2027 – 12/2028 | Experimentos IA, correlación métrica/log/traza, prototipo inicial | Prototipo inicial implementado en GIDAS |
| **F3 — Prototipo escalable** | 01–12/2029 | Escalabilidad, impacto, transferencia | Plataforma validada + 2 laboratorios adoptantes |
| **F4 — Cierre y comunidad** | 2029 – 03/2030 | Publicaciones, PI, comunidad open-source | Informe final + release estable Apache-2.0 |

**Stack del MVP (ADR-0009):** React + TypeScript · FastAPI · SQLModel · **PostgreSQL 16** · Alembic ·
Docker/Podman · VM Rocky 10. CI verde en todo PR · coverage ≥ 70%.

**MVP-0 (F0):** RUM + sondas sintéticas + **modelos de IA (incluidos)**. El MVP-0 instala la captura
RUM, las sondas de disponibilidad y el motor de detección (Isolation Forest + z-score) con health
score, sobre el stack PostgreSQL. (Ver §4.)

---

## 2. Línea operativa: EDT de 8 sprints (24/08 – 13/12/2026)

Fuente: `docs/business/EDT intellops.md`. Sprints de 2 semanas desde el **24/08/2026**.

| Sprint | Fechas | Objetivo principal |
|--------|--------|--------------------|
| **S1** | 24/08 – 06/09/2026 | Arquitectura + infraestructura + contratos |
| **S2** | 07/09 – 20/09/2026 | Backend core + ingesta RUM |
| **S3** | 21/09 – 04/10/2026 | Sesiones + métricas + procesamiento |
| **S4** | 05/10 – 18/10/2026 | ML + modelos + entrenamiento |
| **S5** | 19/10 – 01/11/2026 | Anomalías + alertas + hardening backend |
| **S6** | 02/11 – 15/11/2026 | Integración backend completa + frontend base |
| **S7** | 16/11 – 29/11/2026 | Frontend completo |
| **S8** | 30/11 – 13/12/2026 | Integración final + testing + deploy |

**Hitos internos del EDT:** MVP técnico del backend + IA al cierre de **S5**; el frontend no inicia
hasta **S6**. Issues del plan asociado: S1–S3 en `docs/business/issues-s1-s2.md` y
`docs/business/issues-s2-s3.md`; S2 y S3 publicadas en GitHub como **#35–#45**.

---

## 3. Mapeo de los hitos M0–M4 al marco F0–F4 / EDT

El plan raíz de la dirección usa una numeración anterior de los hitos. El plan integral v1.0
(17/10/2026) y, desde D11 (24/10/2026), el repo adoptan la numeración del Gantt. La tabla mapea la
numeración adoptada e indica su equivalente en el doc raíz.

| Hito (D11) | Equivalente doc raíz | Qué cierra | Fecha | Fase roadmap | Tramo EDT |
|-----------------|-----------|-------|--------------|-----------|-----------|
| **M0** | M0 | Contratos aprobados, ADRs, EDT cargado como issues, primer dato de punta a punta visible | 13/11/2026 | F0 | S2–S6 |
| **M1 — Feature freeze** | — (nuevo) | Todas las funciones de la v1 integradas en `develop`; alcance cerrado | 04/12/2026 | F0 | S5–S8 |
| **M2 — Entrega MVP v1** | M1 | Sitio piloto medido con RUM + sondas; demo ante GIDAS; alerta por Telegram; tests ≥ 70 %; informes finales de PPS | 18/12/2026 | F0 (salida de MVP-0) | S5–S8 |
| **M3 — v1.1** | M2 | Detección ML sobre series con datos reales + dashboard; **dataset etiquetado como condición de entrada**; sondas TLS/DNS/multi-origen; ISP/ASN; User Health Score | 16/04/2027 | F1 | post-EDT |
| **M4 — v2.0** | M3 | LLM local (RCA), 3 sitios piloto, prueba SUS, paper y extensión | 11/06/2027 | F1 | post-EDT |

> El prototipo 2027–2028 del roadmap F2 queda como extensión post-v2.0, fuera de la secuencia M0–M4.
> La numeración anterior del doc raíz se conserva en la segunda columna para trazabilidad.

---

## 4. MVP-0 = RUM + sondas + modelos de IA

> **Vigencia (24/10/2026).** Esta definición corresponde a la numeración anterior y a un MVP-0 con
> modelos de IA. **D1 la revisó**: la v1/M2 usa reglas de umbral (B.14) y la detección ML pasa a
> M3 (v1.1). La definición vigente de alcance es `docs/business/brief-v1.md` §3. El texto se
> conserva como registro de la definición anterior.

**Definición del MVP-0 (F0):** el primer entregable operativo en GIDAS incluye los **modelos de IA**,
no solo la captura. Sus componentes:

1. **RUM** — agente de captura de experiencia de usuario (Core Web Vitals, errores JS).
2. **Sondas** — chequeos sintéticos de disponibilidad (HTTP/TLS/DNS).
3. **Modelos de IA** — detección de anomalías (Isolation Forest + z-score) y health score.

Esta definición reemplaza las lecturas parciales previas del brief (`MVP-0` limitado a captura/almacenamiento
y `MVP-1` para ML) y del roadmap (`MVP-0` sin IA). Es la única definición vigente de MVP-0.

---

## 5. Dueños: tres mapas vigentes

El repositorio convive con **tres asignaciones de dueños** que responden a contextos distintos. No se
unifican en un único RACI: cada mapa gobierna su propio alcance.

| Contexto | Fuente | Federico | Santiago | Romeo |
|----------|--------|----------|----------|-------|
| **PPS2 / TEAM_CHARTER** (módulos PPS) | planes PPS2 | Seguridad | QA | ML |
| **EDT** (`docs/business/EDT intellops.md`) | EDT develop | Telemetría / RUM / Procesamiento | Core Backend / Datos / Seguridad | IA / Anomalías / Alertas |
| **Frentes** (doc raíz + roadmap) | F1/F2/F3 | F1 Captura | F2 Plataforma | F3 Inteligencia |

**Nota de contexto por mapa:**

- **PPS** describe la **entrega evaluable individual** de cada pasantía (200 hs, actividades A1–A7).
- **EDT** describe el **ownership técnico por dominio** en la línea operativa de sprints.
- **Frentes** describe la **organización del equipo** en tres frentes paralelos con dueño y respaldo
  (F1 Captura → Federico, respaldo Romeo; F2 Plataforma → Santiago, respaldo Federico;
  F3 Inteligencia → Romeo, respaldo Santiago; Producto/arquitectura → Emanuel).

Los tres mapas coexisten: PPS = evaluación académica; EDT = operación por dominio; frentes = coordinación
del equipo. Toda ratificación de un ownership único queda como decisión pendiente (§8, GAPS).

---

## 6. Hitos con fechas

### 6.1. Hito 50 % por integrante (PPS)

| Integrante | Hito 50 % | Evidencia |
|------------|-----------|-----------|
| Federico Cavallero | **17/08/2026** (Sem 11, ~120 hs) | IP N°2: Lynis ≥ 70 % |
| Santiago Montanari | **17/08/2026** (Sem 11, ~120 hs) | IP N°2: cobertura ≥ 70 % |
| Romeo Monfroglio | **~14/07/2026** (Sem 10) | Hito 50 % del plan ML |

### 6.2. Hitos de gestión

| Hito | Fecha | Referencia |
|------|-------|------------|
| Arranque EDT (S1) | 24/08/2026 | `docs/business/EDT intellops.md` |
| Corrección de SQLite → PostgreSQL | 11/09/2026 | ADR-0009 (§1) |
| Cierre PPS Romeo (ventana original) | 18/09/2026 | plan PPS2 |
| Cierre PPS Federico y Santiago (ventana original) | 19/10/2026 | plan PPS2 |
| **Informes finales de PPS** | 18/12/2026 | Gantt v1.0 (D13) |
| **M0** | 13/11/2026 | doc raíz |
| **M1 — Feature freeze** | 04/12/2026 | Gantt v1.0 (D11) |
| **M2 — Entrega MVP v1** | 18/12/2026 | Gantt v1.0 (D11) |
| **M3 — v1.1** | 16/04/2027 | Gantt v1.0 (D11) |
| **M4 — v2.0** | 11/06/2027 | Gantt v1.0 (D11) |
| Cierre EDT (S8) | 13/12/2026 | `docs/business/EDT intellops.md` |
| **MVP-0** entregado | 06–12/2026 | roadmap F0 |
| **MVP-1** (SUS > 75) | 01–06/2027 | roadmap F1 |
| Prototipo inicial (F2, extensión post-v2.0) | 07/2027 – 12/2028 | roadmap F2 |
| Cierre formal del PID | 31/03/2030 | roadmap F4 |

---

## 7. Indicadores y riesgos

### 7.1. Tablero de indicadores

Base: KPIs por fase del `roadmap-producto.md` §9 + criterios de aceptación de `marco/04-especificaciones.md` §6.

| Indicador | F0 | F1 | F2 | F3 | F4 | Verificación |
|-----------|----|----|----|----|----|--------------|
| Demo de punta a punta al cierre de sprint | 100 % sprints | 100 % | — | — | — | Tablero de issues |
| PRs con revisión cruzada | 100 % | 100 % | — | — | — | Historial de PRs |
| Issues vinculados a un hito | 100 % de los que entran al sprint | 100 % | — | — | — | Etiquetas M0–M4 |
| Frentes con dueño y respaldo | 3 de 3 | 3 de 3 | — | — | — | §5 |
| Cumplimiento del objetivo de sprint | ≥ 80 % | ≥ 80 % | — | — | — | Sprint review |
| Coverage | ≥ 70 % | ≥ 70 % | ≥ 70 % | ≥ 75 % | ≥ 75 % | pytest-cov (gate) |
| F1 (anomalías) | — | ≥ 0.70 | ≥ 0.75 | ≥ 0.80 | ≥ 0.80 | Dataset de validación |
| Time-to-anomaly | — | < 10 s | < 8 s | < 8 s | < 8 s | Tarea medida |
| SUS (4 personas académicas) | — | > 75 | > 75 | > 78 | > 78 | Cuestionario |
| Uptime del stack | > 99 % | > 99.5 % | > 99.5 % | > 99.5 % | > 99.5 % | Healthchecks + Netdata (post-MVP) |
| Costo operativo mensual | $0 | $0 | $0 | $0 | $0 | Tracking |
| Laboratorios adoptantes | 0 | 0 | 0 | 2+ | 2+ | Acuerdos |
| Publicaciones | 0 | 3 borradores | 2 papers | 2+ papers | 4+ publicaciones | Repositorio |

### 7.2. Registro de riesgos

Base: riesgos del `roadmap-producto.md` §10 + riesgos y supuestos de `marco/04-especificaciones.md`.

| Riesgo | Fase | Mitigación |
|--------|------|------------|
| PPS terminan (oct 2026) sin entregables completos | F0 | Contratos publicados temprano; seguimiento semanal; DoD único |
| El stack no entra en 2 GB de RAM (core + ai-engine + comms + PostgreSQL; el stack LGTM de producto es roadmap y el GLP de seguridad corre aparte) | F0/F1 | Medir con `docker stats` en M2; tuning conservador; presupuesto de recursos por contenedor |
| Alcance que crece hacia ML y LLM antes de tener datos | M3/M4 | Dataset etiquetado como condición de entrada |
| Salida del equipo antes del handover | F0 | Handover como requisito de salida; mantenedor técnico estable (ver `governance/continuity.md`) |
| Sondas desde una sola red | M1 | Al menos dos puntos de origen |
| Licencia de la base de ASN y geolocalización | F1/M3 | Verificar antes de M3 y registrar la decisión en un ADR |
| Resultados de experimentos no cumplen el objetivo F1 | F2 | Baselines livianos primero (IF/z-score); LSTM como extensión; datasets versionados |
| Adopción externa lenta | F3 | Convenios por dirección GIDAS; demo pública read-only; deploy < 30 min |
| Free-tier cloud expira (AWS 12 meses) | F1+ | GCP perpetuo + self-hosted completo en VM |
| Cambios de stack posteriores (post-PID) | F4 | ADRs vivos; repositorios con interfaz; especificaciones versionadas |

---

## 8. GAPS abiertos

1. **Horas sin estimar.** El conteo de horas existe solo por actividad PPS (600 hs directas). El EDT y
   el backlog **no tienen horas por tarea**: solo una "talla ref." cualitativa (S≤8 / M≤16 / L≤40 / XL>40)
   pendiente de planning poker. No se puede sumar el plan de desarrollo fuera de los PPS.
2. **Ownership sin ratificar.** Los tres mapas de dueños (§5) siguen sin unificación. Falta ratificar
   un ownership único o la regla de precedencia entre ellos.
3. **Calendarios desfasados.** PPS arrancan 01/06/2026 (Romeo 04/05); el EDT arranca 24/08/2026; los
   sprints del doc raíz van del 19/10 al 18/12/2026 y la entrega (M2 adoptado) en 18/12. No hay un único eje temporal.
4. **Stack PPS vs repo.** Federico PPS2 v2 = ELK/Kibana vs cronograma v3 GRAFANA vs ADR-0001 GLP;
   Romeo PPS usa TimescaleDB + LSTM/Prophet vs repo PostgreSQL/SQLModel + IF+z-score y health score
   no planificado en PPS; Santiago PPS dice GitLab CI vs repo GitHub Actions. Falta actualizar los PPS2.
5. **Actividades sin horas y/o dueño.** Tareas del EDT sin horas ni fecha; E05/E06/E10/E11/E12 y varios
   ítems con owner "X (transversal/coordinación)"; F0-7 "Romeo + Ema" y F0-8 "Coordinación" sin horas.
6. **Fechas de fin discrepantes.** Romeo cierra 18/09/2026; Federico/Santiago 19/10/2026; MVP-0 roadmap
   = oct 2026; M2 adoptado (M1 del doc raíz) = 18/12/2026; MVP-1 = jun 2027. Falta fijar el fin de cada frente.
7. **"Embedded content" sin tablas.** Roadmap, EDT, cronograma y Gantt del doc raíz están descritos,
   no volcados como tablas: no se pueden extraer fechas y tareas exactas (este plan reconstruye desde
   las fuentes reales, no desde el doc).
8. **Errores de copiado en insumos.** La firma del cronograma v2 de Federico dice "Romeo Monfroglio
   Leg. 31729"; las solicitudes de inicio de Federico y Santiago dicen "Proveedor de Soluciones: Romeo
   Monfroglio". Normalizar nombres/legajos al consolidar.
9. **Único registro de horas reales.** El Informe de Avance 1 (may–jul 2026) estima ~245 hs (Emanuel
   ~126 · Federico ~46 · Romeo ~42 · Santiago ~31). No cubre jun–oct completo ni mapea a A1–A7.
10. **Hito 50 % sin línea base común.** Los hitos 50 % no coinciden entre integrantes (Romeo ~14/07,
    Federico/Santiago 17/08) ni con MVP-0 (oct 2026). Falta una tabla única de hitos (ver §6.1).

---

## Referencias

- `gestionProyecto/roadmap/roadmap-producto.md` — roadmap F0–F4 y KPIs por fase.
- `gestionProyecto/roadmap/roadmap-mvp-pps.md` — acotamiento a la ventana PPS.
- `gestionProyecto/marco/04-especificaciones.md` — criterios de aceptación e indicadores.
- `docs/adr/0009-postgresql-16-como-base-de-datos.md` — stack de almacenamiento del MVP.
- `docs/business/EDT intellops.md` — EDT operativo de 8 sprints.
- `docs/business/comparacion-plan-gestion-edt-vs-develop.md` — contraste con el doc raíz.
- `governance/continuity.md` — continuidad, handover y cohorte.
- `docs/brief-v2.md` — brief de producto (stack corregido a PostgreSQL).
