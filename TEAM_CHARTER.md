# Team Charter — IntellOps

## Identidad del Proyecto

| Campo | Valor |
|-------|-------|
| **Proyecto** | IntellOps — Sistema de Observabilidad Predictiva UX-Céntrica + AI/LLM Open-Source |
| **Código** | GIDAS-InfraIT-2026-IntellOps |
| **Tipo** | PI+D+i (Proyecto de Investigación, Desarrollo e Innovación) |
| **Grupo** | GIDAS (Grupo de Investigación y Desarrollo Aplicado a Sistemas Informáticos y Computacionales) |
| **Unidad Académica** | UTN Facultad Regional La Plata (UTN-FRLP) |
| **Sub-proyecto** | InfraIT |
| **Línea de Investigación** | Sistemas Inteligentes de Infraestructura IT — Ingeniería de Recursos Escasos |
| **Enfoque I+D+i** | Observabilidad centrada en el usuario: anticipar reclamos e incidencias de usuarios reales mediante OpenTelemetry + Grafana LGTM + Agentes IA + Alertas multicanal |

## Miembros del Equipo

| Rol | Nombre | Módulo | Período | Contacto |
|-----|--------|--------|---------|----------|
| **Coordinador / Arquitecto** | Emanuel Rodriguez | Dirección técnica, SDD, GitHub, visión I+D+i | 2026-2027 | @ema |
| **Director / Sponsor** | Ing. Leopoldo Nahuel | Dirección académica, laboratorio GIDAS | 2026-2027 | — |
| **Desarrollador — User Telemetry** | Federico Blanco Cavallero | **Fase 1**: Seguridad (hardening CIS, GLP, dashboards). **Fase 2**: User Telemetry & Tracing (agente RUM OTel, Tempo, alertas multicanal) | Jun-Oct 2026 | @fcavallero |
| **Desarrollador — ML/AI Agents** | Romeo Lorenzo Monfroglio | **Fase 1**: ML clásico (detección anomalías, Isolation Forest). **Fase 2**: Agentes IA para UX Predictiva (RCA, User Health Score, clasificador de reclamos) | May-Sep 2026 | @rmonfroglio |
| **Desarrollador — QA/Observability** | Santiago Montanari | **Fase 1**: QA + CI/CD (testing, pipelines, quality gates). **Fase 2**: Observability-Driven QA (synthetic journeys OTel, chaos engineering, CBAs) | Jun-Oct 2026 | @smontanari |

## Valores del Equipo

1. **Calidad > Cantidad** — Preferimos un PR bien testeado y documentado a tres PRs apurados.
2. **Contrato > Código** — Las specs se escriben y validan antes de implementar. El código sigue al contrato, no al revés.
3. **Aprendizaje > Entregable** — Somos un equipo de investigación. El conocimiento generado vale tanto como el software producido.
4. **Comunicación Asíncrona > Reuniones** — Preferimos issues, PRs y docs a reuniones sin orden del día.
5. **Recursos Escasos, Resultados Abundantes** — Operamos con hardware modesto y free-tier cloud. Es una restricción de diseño, no una excusa.
6. **Ciencia Abierta** — Código, datos y experimentos son públicos y reproducibles. Todo puede ser revisado, replicado y mejorado.

## Acuerdos de Trabajo

- **Daily**: Async vía issue/comentario en GitHub antes de las 10am.
- **Sprint Review**: Viernes cada 2 semanas, demo de lo completado.
- **Retro**: Post-sprint, 30 min, enfocado en mejora continua.
- **Comunicación**: Issues de GitHub para decisiones técnicas, Slack/Discord para lo urgente.
- **Decisiones**: Cualquier decisión técnica se documenta en un ADR (`docs/adr/`). Sin ADR, la decisión no existe.

## Estructura de Trabajo: Fase 1 + Fase 2

Cada contributor completa **Fase 1** (fundamentos de infra) antes de pasar a **Fase 2** (observabilidad UX-céntrica). Las fases son secuenciales: no se salta la Fase 1, pero el objetivo final es la Fase 2.

- **Fase 1**: Construcción de base técnica sobre infraestructura real del laboratorio GIDAS
- **Fase 2**: Investigación e implementación de observabilidad predictiva centrada en el usuario con OpenTelemetry + LGTM + AI Agents

## Definiciones de "Hecho" (DoD)

| Dimensión | Criterio |
|-----------|----------|
| **Spec** | OpenAPI 3.1 / AsyncAPI 3.0 validado, revisado por pares, mergeado a `develop` |
| **Código** | Passes tests (unit + integration + contract), coverage >= 70%, linter ok |
| **ML** | F1 > 0.80 o MAPE < 15%, reproducible con seed fijo, reporte generado |
| **Documentación** | ADR escrito, sección en onboarding actualizada, changelog entry |
| **Investigación** | Notebook exportable, experimento versionado en DVC/MLflow, paper outline |
| **Release** | SBOM generado, CITATION.cff actualizado, tag semántico, release notes |
| **Fase 2 (adicional)** | Trazas OTel validadas en Tempo, quality gates OTel en CI, User Health Score documentado |

## Canales de Comunicación

| Canal | Propósito |
|-------|-----------|
| GitHub Issues | Decisiones técnicas, bugs, propuestas de cambio |
| GitHub Discussions | Debate abierto, investigación, preguntas |
| GitHub PRs | Review de código y specs |
| Slack/Discord | Urgencias, dudas rápidas, social |

---

*Este charter es un documento vivo. Se revisa al inicio de cada fase del roadmap.*
