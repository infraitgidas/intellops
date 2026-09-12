# IntellOps — Documento para el Negocio (Propuesta de Valor)

**Documento**: `audiencias/negocio.md`
**Fecha**: 2026-09-11
**Autor**: Coordinación InfraIT — Emanuel Rodríguez
**Audiencia**: dirección (UTN/GIDAS), adoptantes potenciales (pymes, empresas, organismos), decisores económicos.
**Idioma del valor**: costo, riesgo, retorno, transferencia — no arquitectura.

---

## 1. El problema de negocio

| Hecho | Consecuencia |
|---|---|
| Las plataformas comerciales de observabilidad cuestan **$50K-$2M por año** (Datadog, Dynatrace, New Relic) | Las pymes y los laboratorios no pueden acceder |
| Esas plataformas **miran la infraestructura, no al usuario** | Se detecta la falla cuando el usuario ya la padeció |
| La producción de software asistida por IA **acelera la complejidad** de las infraestructuras | Los dashboards legacy no se mantienen al ritmo |
| Las herramientas OSS solas requieren **expertise SRE** que las pymes no tienen | La adopción de open source se frustra |

**El costo oculto del monitoreo tradicional**: no es la licencia, es la **falla no anticipada** — reclamos,
pérdida de confianza, horas de equipo apagando incendios en vez de construyendo.

---

## 2. La propuesta de valor de IntellOps

> **Observabilidad predictiva centrada en el usuario, de costo $0/mes, reproducible en < 30 minutos.**

| Dimensión | Oferta de IntellOps | Contraste con el mercado |
|---|---|---|
| **Costo** | $0/mes de operación (OSS + free-tier + hardware propio) | Datadog $500K-$2M/año |
| **Enfoque** | El **usuario** es la referencia: experiencia → producto → infraestructura | Todos miran servidores |
| **IA** | Isolation Forest + z-score (baseline) y LLM **local** cuantizado (RCA, sin APIs externas) | IA en la nube de pago |
| **Recursos** | < 2GB RAM, CPU dual-core, **sin GPU** — hardware legacy GIDAS | Requieran infra media/alta |
| **Reproducibilidad** | `docker compose up` (o podman) con datos seed | Paquetes/cloud owners |
| **Transparencia** | Specs públicas, experimentos versionados, ADRs | Cajas negras |

**La ventaja diferencial no es tecnológica: es de ENFOQUE.** Mientras Datadog observa el sistema,
IntellOps observa *al usuario del sistema* — y reconstruye la cadena causal completa para anticipar.

---

## 3. Retorno esperado (para adoptantes)

### 3.1. KPIs de valor generado (objetivo, del marco)

| KPI | Target | Qué significa para la organización |
|---|---|---|
| Time-to-anomaly que impacta UX | < 10 s | La falla se detecta **antes** de que el usuario la sufra |
| Health Score vs reclamos reales | r > 0.75 | La métrica de salud **predice** el nivel de reclamos |
| F1 detección de anomalías | ≥ 0.70 | Más de 7 de cada 10 anomalías reales se detectan con precisión aceptable |
| Precisión factual del RCA asistido | ≥ 80% | El equipo deja de adivinar causa raíz: el asistente la documenta |
| Cobertura de tests críticos | ≥ 70% | Menos regresiones, más confianza para liberar |
| Lynis compliance post-hardening | ≥ 70% | Postura de seguridad auditable y mejorada |
| Costo operativo mensual | $0 | El proyecto no compite por presupuesto operativo |

### 3.2. Escenario de adopción típico (pyme/laboratorio)

| Paso | Esfuerzo | Resultado |
|---|---|---|
| Levantar stack en VM propia | < 30 min (`docker compose up`) | Plataforma operativa |
| Conectar app/servicios (OTel) | 1-2 días por servicio | Métricas, logs y trazas fluyen |
| Conectar frontend (agente RUM) | ½ día (bundle < 30KB) | Experiencia UX capturada |
| Entrenar baseline de anomalías | Automático (seed + umbrales) | Detección activa el primer día |

**Costo total de adopción**: $0 de licencias + horas de integración (las mismas que se invertirían en cualquier
observabilidad, pero modelos configurados ya).

---

## 4. Presupuesto del PID (contexto de financiamiento)

| Concepto | Monto (PID 2027-2030) | Destino |
|---|---|---|
| Equipamiento / otros | $11.016.000 | Infraestructura de investigación |
| RRHH (becarios: Cáceres Petkowicz, otros) | $50.000.000 | Formación de recursos humanos |
| **Total financiado** | **$61.016.000** | PID TC GIDAS |
| **Operación técnica IntellOps** | **$0 adicionales** | Open-source + free-tier + hardware existente |

El presupuesto del PID financia **personas y publicaciones**; la plataforma misma no consume presupuesto operativo.
Esto es deliberado: el prototipo debe ser sostenible **después** del PID, en cualquier institución adoptante.

---

## 5. Riesgos del negocio y mitigación

| Riesgo | Mitigación |
|---|---|
| Adopción externa lenta (2029) | Convenios por dirección GIDAS; demo pública read-only; deploy < 30 min; talleres de formación |
| Resultados de IA por debajo del umbral (F1 < 0.70 en ciertos datasets) | Baselines livianos primero (IF/zscore); LSTM como extensión documentada; datasets versionados para honestidad científica |
| Fin del free-tier cloud (AWS 12 meses) | GCP perpetuo + self-hosted completo en VM (ninguna dependencia de nube) |
| El equipo cambia después del PID | Documentación viva, ADRs, especificaciones versionadas; el conocimiento vive en el repo, no en las cabezas |
| Competencia OSS (SigNoz, OpenObserve) sube el nivel | Competimos en **enfoque UX + costo $0 + reproducibilidad académica**, que los OSS comerciales no persiguen |

---

## 6. Casos de uso comerciales concretos

1. **Pyme SaaS multi-tenant**: detectar qué *tenant* está degradando la experiencia antes del reclamo → retención.
2. **Laboratorio/UTN**: correlacionar el estado de la infraestructura académica con el uso real de las apps → diagnóstico y papers.
3. **Empresa con equipos chicos**: un solo stack OSS que reemplaza 3 herramientas pagas, con IA incluida → ahorro directo.
4. **Organismo con datos sensibles**: GenIA local (sin APIs externas) para RCA → cumplimiento y privacidad.

---

## 7. Cómo medimos el éxito (indicadores del programa)

| Fase | Indicador de negocio |
|---|---|
| F0 (2026, PPS) | MVP-0 operativo; 3 PPS aprobadas con entregables mapeados al backlog |
| F1 (2027) | MVP-1 con SUS > 75; 3 papers base; costo $0 verificado |
| F2 (2028) | Prototipo inicial; 2+ papers con evidencia experimental |
| F3 (2029) | Plataforma en 2+ laboratorios adoptantes; talleres realizados |
| F4 (2030) | Release Apache-2.0 + informe final + comunidad activa |

---

*Documento vivo. Se revisa en cada hito de fase y ante cambios aprobados por dirección GIDAS.*