# Onboarding — Federico Cavallero (Módulo Seguridad)

¡Bienvenido al equipo! Este es tu plan de onboarding específico para arrancar con el Módulo de Seguridad de IntellOps.

## Tu Rol

Diseñar e implementar el **módulo de seguridad** de IntellOps:
- Hardening CIS Benchmark Level 1 sobre la infraestructura del laboratorio GIDAS
- Pipeline de logs de seguridad con **Grafana + Loki + Prometheus** (reemplazo de ELK, ver ADR-0001)
- 4 dashboards de seguridad en Grafana
- Automatización con Ansible

## Tus Primeros Pasos

### Semana 1 — Conocé el Proyecto (días 1-3)

- [ ] Aceptá la invitación de GitHub: https://github.com/infraitgidas/intellops/invitations
- [ ] Cloná el repo y seguí el [onboarding general](README.md)
- [ ] Leé estos documentos en orden:
  1. `TEAM_CHARTER.md` — conocé al equipo y los valores
  2. `docs/brief-v2.md` — contexto completo del proyecto
  3. `openspec/specs/research/hypotheses.md` — línea L3 (tu hipótesis de investigación)
  4. `openspec/specs/architecture/containers.md` — entendé el stack completo
  5. `docs/adr/0001-reemplazo-elk-por-grafana-loki-prometheus.md` — por qué cambiamos ELK por GLP
- [ ] Ejecutá `make setup` y `make up` para ver el API funcionando
- [ ] Corré `make test` — todo verde ✅

### Semana 1 — Investigación y Baseline (días 4-5)

- [ ] Ejecutá Lynis en tu máquina para conocer la herramienta: `sudo lynis audit system`
- [ ] Investigá: ¿qué es CIS Benchmark Level 1? ¿qué controles aplican a nuestro stack?
- [ ] Leé sobre Promtail + Loki + Grafana — cómo se configura un pipeline de logs
- [ ] Anotá preguntas para la daily del equipo

### Semana 2 — Primer Cambio SDD

Tu primer cambio va a ser: **documentar el estado actual de seguridad del laboratorio GIDAS**.

Seguí el flujo SDD:

```bash
# 1. Creá un issue de tipo "Change Proposal"
#    https://github.com/infraitgidas/intellops/issues/new?template=02-change-proposal.md
#    Título: "[change] baseline-seguridad-gidas"

# 2. Esperá la review del coordinador

# 3. Cuando esté aprobado, creá tu rama
git checkout develop
git pull origin develop
git checkout -b feat/baseline-seguridad develop

# 4. Implementá tu cambio
#    - Auditoría inicial con Lynis
#    - Documentación del estado actual en docs/research/exp-201-baseline.md
#    - ADR si es necesario

# 5. PR a develop
git add -A
git commit -m "feat: baseline de seguridad laboratorio GIDAS"
git push origin feat/baseline-seguridad
# Abrí PR en GitHub con el template
```

## Documentos Clave para tu Módulo

| Documento | Por qué es importante |
|-----------|----------------------|
| `openspec/specs/research/hypotheses.md` (H3) | Tu hipótesis con criterios de validación |
| `openspec/specs/research/experiments.md` (EXP-201 a 203) | Tus experimentos planificados |
| `docs/adr/0001-reemplazo-elk-por-grafana-loki-prometheus.md` | Stack de seguridad definido |
| `governance/compliance.md` | Política de licencias que afectan tu módulo |
| `openspec/specs/architecture/interfaces.md` | Puertos y endpoints que vas a necesitar |

## Stack Específico

| Herramienta | Propósito | Estado |
|-------------|-----------|--------|
| Lynis / OpenSCAP | Auditoría de seguridad | Investigar |
| Ansible | Automatización de hardening | Investigar |
| Promtail | Recolección de logs | Por configurar |
| Loki | Almacenamiento de logs | Por configurar |
| Grafana | Dashboards de seguridad | Por configurar |
| CIS Benchmark | Guía de hardening | Investigar |

## Referencias Rápidas

- [CIS Benchmarks](https://www.cisecurity.org/cis-benchmarks)
- [Lynis Documentation](https://cisofy.com/documentation/lynis/)
- [Loki Documentation](https://grafana.com/docs/loki/latest/)
- [Promtail Documentation](https://grafana.com/docs/loki/latest/clients/promtail/)
- [Grafana Dashboards](https://grafana.com/docs/grafana/latest/dashboards/)

## Checklist de Avance

- [ ] Semana 1: Onboarding completo + lectura de docs
- [ ] Semana 2: Baseline de seguridad documentado (primer cambio SDD)
- [ ] Semana 5: Informe Parcial 1 (baseline + ADRs)
- [ ] Semana 11: Hardening CIS completo (Hito 50%)
- [ ] Semana 15: Pipeline GLP operativa
- [ ] Semana 19: Dashboards Grafana integrados
- [ ] Semana 20: Informe Final + Paper CACIC/JAIIO

---

*¿Dudas? Abrí un issue con label `setup` o hablá con el coordinador.*
