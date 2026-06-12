# Onboarding — Federico Cavallero

¡Bienvenido al equipo! Este onboarding tiene **dos fases** secuenciales: primero construís los fundamentos de infraestructura, y después aplicás ese conocimiento a la observabilidad centrada en el usuario.

---

## Fase 1: Fundamentos de Infra (Sprint 1-2)

Diseñar e implementar el **módulo de seguridad** de IntellOps sobre infraestructura real del laboratorio GIDAS.

### Tu Rol en Fase 1

- Hardening CIS Benchmark Level 1 sobre la infraestructura del laboratorio GIDAS
- Pipeline de logs de seguridad con **Grafana + Loki + Prometheus** (reemplazo de ELK, ver ADR-0001)
- 4 dashboards de seguridad en Grafana
- Automatización con Ansible

### Semana 1 — Conocé el Proyecto (días 1-3)

- [ ] Aceptá la invitación de GitHub: https://github.com/infraitgidas/intellops/invitations
- [ ] Cloná el repo y seguí el [onboarding general](README.md)
- [ ] Leé estos documentos en orden:
  1. `TEAM_CHARTER.md` — conocé al equipo y los valores
  2. `docs/brief-v2.md` — contexto completo del proyecto
  3. `openspec/specs/research/hypotheses.md` — línea L3 (tu hipótesis de Fase 1)
  4. `openspec/specs/architecture/containers.md` — entendé el stack completo
  5. `docs/adr/0001-reemplazo-elk-por-grafana-loki-prometheus.md` — por qué cambiamos ELK por GLP
- [ ] Ejecutá `make setup` y `make up` para ver el API funcionando
- [ ] Corré `make test` — todo verde ✅

### Semana 1 — Investigación y Baseline (días 4-5)

- [ ] Ejecutá Lynis en tu máquina para conocer la herramienta: `sudo lynis audit system`
- [ ] Investigá: ¿qué es CIS Benchmark Level 1? ¿qué controles aplican a nuestro stack?
- [ ] Leé sobre Promtail + Loki + Grafana — cómo se configura un pipeline de logs
- [ ] Anotá preguntas para la daily del equipo

### Documentos Clave para Fase 1

| Documento | Por qué es importante |
|-----------|----------------------|
| `openspec/specs/research/hypotheses.md` (H3) | Tu hipótesis de Fase 1 con criterios de validación |
| `openspec/specs/research/experiments.md` (EXP-201 a 203) | Tus experimentos de Fase 1 planificados |
| `docs/adr/0001-reemplazo-elk-por-grafana-loki-prometheus.md` | Stack de seguridad definido |
| `governance/compliance.md` | Política de licencias que afectan tu módulo |
| `openspec/specs/architecture/interfaces.md` | Puertos y endpoints que vas a necesitar |

### Stack Específico — Fase 1

| Herramienta | Propósito | Estado |
|-------------|-----------|--------|
| Lynis / OpenSCAP | Auditoría de seguridad | Investigar |
| Ansible | Automatización de hardening | Investigar |
| Promtail | Recolección de logs | Por configurar |
| Loki | Almacenamiento de logs | Por configurar |
| Grafana | Dashboards de seguridad | Por configurar |
| CIS Benchmark | Guía de hardening | Investigar |

---

## Fase 2: Observabilidad UX-Céntrica con OpenTelemetry (Sprint 3+)

Una vez que entendés cómo se monitorea un server con logs y métricas, pasamos al siguiente nivel: **instrumentar la experiencia del usuario real** para anticipar reclamos antes de que ocurran.

### Tu Rol en Fase 2

| Actividad I+D+i | Por qué es investigación | Qué vas a construir |
|----------------|-------------------------|---------------------|
| **Agente RUM ultra-liviano con OTel** | No existe un agente RUM open-source < 30KB que respete privacidad en contextos académicos | Agente JS que captura Core Web Vitals + trazas OpenTelemetry + errores de frontend |
| **Pipeline de tracing distribuido OTel + Tempo** | Cómo correlacionar trazas de frontend → backend → DB en recursos limitados es un problema abierto | Instrumentación OTel en FastAPI + agente RUM → export a Tempo |
| **Sistema de alertas multicanal** | Diseñar un alerting router inteligente que decida canal según severidad y horario | Módulo de notificaciones con templates y routing por canal (Mail, Telegram, WhatsApp) |
| **Correlación traza-usuario** | Vincular una traza técnica con un usuario real respetando anonimización | Context propagation con user-id anonimizado |

### Semana 3-4 — Investigación y Prototipado

- [ ] Leé la especificación H5 en `openspec/specs/research/hypotheses.md`
- [ ] Revisá los experimentos EXP-OTel-01 a 04 en `openspec/specs/research/experiments.md`
- [ ] Investigá OpenTelemetry JS SDK: https://opentelemetry.io/docs/languages/js/
- [ ] Armá un PoC de agente RUM que capture LCP, INP, CLS y lo envíe a un collector OTel local
- [ ] Configurá OpenTelemetry Collector con export a Loki y Tempo
- [ ] Investigá alert managers open-source: Grafana Alertmanager, ntfy, Apprise

### Semana 5+ — Implementación

```bash
# Primer cambio SDD de Fase 2
# Título: "[change] agente-rum-otel"
git checkout -b feat/agente-rum-otel develop

# Implementación:
# - src/agent/rum.js — Agente RUM con OTel JS SDK
# - src/api/routers/telemetry.py — Endpoint de ingesta OTLP
# - docker-compose.yml — Agregar OTel Collector + Tempo
# - tests/test_rum.py — Tests del agente
```

### Documentos Clave para Fase 2

| Documento | Por qué es importante |
|-----------|----------------------|
| `openspec/specs/research/hypotheses.md` (H5) | Tu hipótesis de Fase 2 |
| `openspec/specs/research/experiments.md` (EXP-OTel-*)| Tus experimentos de telemetría |
| `openspec/specs/architecture/containers.md` | Tempo, OTel Collector, Alertmanager agregados |
| `docs/adr/` | ADRs de decisiones de instrumentación |

### Stack Específico — Fase 2

| Herramienta | Propósito | Estado |
|-------------|-----------|--------|
| OpenTelemetry JS SDK | Instrumentación de frontend | Investigar |
| OpenTelemetry Collector | Recepción y enrutamiento de señales OTel | Por configurar |
| Tempo | Almacenamiento de trazas distribuidas | Por configurar |
| Grafana Alertmanager | Routing de alertas multicanal | Por configurar |
| Apprise / ntfy | Notificaciones a Telegram, WhatsApp, Mail | Investigar |
| W3C Trace Context | Propagación de contexto entre servicios | Por implementar |

### Checklist de Avance — Fase 2

- [ ] Semana 3-4: PoC agente RUM con OTel + Collector local funcionando
- [ ] Semana 5-6: Pipeline Tempo + Loki operativo con trazas del PoC (primer cambio SDD Fase 2)
- [ ] Semana 8-9: Alertas multicanal integradas (Mail + Telegram + WhatsApp)
- [ ] Semana 12: Correlación traza-usuario funcionando con datos anonimizados
- [ ] Semana 16: Benchmark de overhead de instrumentación completo
- [ ] Semana 20: Informe Final + Paper en conferencia/revista académica

---

## Referencias Rápidas

### Fase 1
- [CIS Benchmarks](https://www.cisecurity.org/cis-benchmarks)
- [Lynis Documentation](https://cisofy.com/documentation/lynis/)
- [Loki Documentation](https://grafana.com/docs/loki/latest/)
- [Promtail Documentation](https://grafana.com/docs/loki/latest/clients/promtail/)
- [Grafana Dashboards](https://grafana.com/docs/grafana/latest/dashboards/)

### Fase 2
- [OpenTelemetry JS SDK](https://opentelemetry.io/docs/languages/js/)
- [OpenTelemetry Collector](https://opentelemetry.io/docs/collector/)
- [Grafana Tempo](https://grafana.com/docs/tempo/latest/)
- [W3C Trace Context](https://www.w3.org/TR/trace-context/)
- [Apprise — Multi-channel notifications](https://github.com/LouiseGrandJean/Apprise)
- [Grafana Alerting](https://grafana.com/docs/grafana/latest/alerting/)

---

*¿Dudas? Abrí un issue con label `setup` o hablá con el coordinador.*
