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

## Miembros del Equipo

| Rol | Nombre | Módulo | Período | Contacto |
|-----|--------|--------|---------|----------|
| **Coordinador / Arquitecto** | Emanuel Rodriguez | Dirección técnica, SDD, GitHub | 2026-2027 | @ema |
| **Director / Sponsor** | Ing. Leopoldo Nahuel | Dirección académica, laboratorio GIDAS | 2026-2027 | — |
| **Desarrollador — Seguridad** | Federico Blanco Cavallero | Módulo de Seguridad (hardening CIS, ELK, dashboards) | Jun-Oct 2026 | @fcavallero |
| **Desarrollador — ML** | Romeo Lorenzo Monfroglio | Módulo ML (detección anomalías, LSTM, Isolation Forest) | May-Sep 2026 | @rmonfroglio |
| **Desarrollador — QA** | Santiago Montanari | Módulo QA (testing automatizado, CI/CD, quality gates) | Jun-Oct 2026 | @smontanari |

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

## Definiciones de "Hecho" (DoD)

| Dimensión | Criterio |
|-----------|----------|
| **Spec** | OpenAPI 3.1 / AsyncAPI 3.0 validado, revisado por pares, mergeado a `develop` |
| **Código** | Passes tests (unit + integration + contract), coverage >= 70%, linter ok |
| **ML** | F1 > 0.80 o MAPE < 15%, reproducible con seed fijo, reporte generado |
| **Documentación** | ADR escrito, sección en onboarding actualizada, changelog entry |
| **Investigación** | Notebook exportable, experimento versionado en DVC/MLflow, paper outline |
| **Release** | SBOM generado, CITATION.cff actualizado, tag semántico, release notes |

## Canales de Comunicación

| Canal | Propósito |
|-------|-----------|
| GitHub Issues | Decisiones técnicas, bugs, propuestas de cambio |
| GitHub Discussions | Debate abierto, investigación, preguntas |
| GitHub PRs | Review de código y specs |
| Slack/Discord | Urgencias, dudas rápidas, social |

---

*Este charter es un documento vivo. Se revisa al inicio de cada fase del roadmap.*
