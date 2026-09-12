# IntellOps — Documento para Interesados (Stakeholders)

**Documento**: `audiencias/interesados.md`
**Fecha**: 2026-09-11
**Autor**: Coordinación InfraIT — Emanuel Rodríguez
**Audiencia**: Dirección GIDAS, dirección de UTN, investigadores, adoptantes, comunidad — quien necesita el "qué" y el "para qué", no el "cómo".

---

## 1. En una hoja

| Aspecto | Respuesta |
|---|---|
| **Qué** | Sistema de observabilidad predictiva centrada en la experiencia del usuario (UX), con IA (AIOps) y costo de operación $0/mes |
| **Por qué** | Las soluciones comerciales cuestan $50K-$2M/año y miran la infraestructura, no al usuario. Las pymes y laboratorios no pueden pagarlas |
| **Quién lo construye** | PID TC GIDAS (UTN FrLP, 2027–2030) + PPS 2026 de 3 colaboradores (Federico/Romeo/Santiago) bajo coordinación InfraIT |
| **Cuándo** | MVP-0 octubre 2026 · MVP-1 validado junio 2027 · prototipo del PID 2028-2029 · transferencia 2029-2030 |
| **Para quién** | Organizaciones que construyen y operan software: laboratorios, pymes, empresas, organismos |
| **Dónde vive** | Repositorio público, documentación abierta, estándares abiertos (OTel, OAS, AsyncAPI, GLP) |

---

## 2. Los interesados y qué les aporta IntellOps

| Stakeholder | Rol | Interés principal | Lo que IntellOps le aporta |
|---|---|---|---|
| **Dirección GIDAS** (Ing. Nahuel) | Director del PID | Publicaciones, transferencia, formación RRHH | Prototipo del PID, papers, casos de estudio, RRHH formado (Fierreros IT/InfraIT) |
| **Coordinación InfraIT** (Emanuel) | Coordinador/arquitecto | Coherencia técnica, visión I+D+i | Marco, especificaciones, backlog, gobernanza Spec-Driven (SDD) |
| **Colaboradores PPS** (Federico, Romeo, Santiago) | Desarrolladores | Aprobar PPS 2026 (200 hs), portfolio, co-autoría | Módulos con criterios claros (DoD), contratos publicados, insumo publicable |
| **Investigadores GIDAS** | Usuarios del sistema | Datos para papers, reproducibilidad | Datasets exportables, experimentos versionados, specs públicas |
| **Usuarios finales de apps GIDAS** | Visita/uso | Que el sistema funcione bien | Protección proactiva: fallas anticipadas antes de que las padezcan |
| **Adoptantes potenciales** (pymes, otras UTN, organismos) | Transferencia | Solución barata y efectiva | Prototipo $0/mes, reproducible < 30 min, sin licencias |
| **Comunidad open source** | Contribución/adopción | Software libre de calidad | Repositorio público Apache-2.0, docs vivas, roadmap público |

---

## 3. Lo que un interesado debe saber (mensajes clave)

1. **Esto no es un proyecto de monitoreo más**: es un proyecto de **investigación aplicada** con entregable de producto. Cada módulo se publica y se transfiere.
2. **El dinero del proyecto alcanza y sobra**: los fondos del PID ($61.016.000 en 3 años) financian RRHH y publicaciones; la **operación técnica cuesta $0/mes** (open-source + free-tier + hardware legacy GIDAS).
3. **El riesgo está gestionado por escrito**: decisiones documentadas en ADR-0001 (GLP en lugar de ELK) y ADR-0002 (PostgreSQL en lugar de SQLite) con alternativas, consecuencias y mitigaciones.
4. **Las PPS 2026 son el primer hito verificable**: en octubre de 2026 hay un MVP-0 corriendo en el laboratorio GIDAS, con seguridad hardening, ML de anomalías y calidad CI/CD — no una promesa.
5. **Preguntas que deben hacerle al equipo** (y que el equipo responde en este repositorio):
   - ¿Qué evidencia hay de que detectamos anomalías antes que el usuario? → KPIs: time-to-anomaly < 10s, F1 ≥ 0.70.
   - ¿Qué cuesta operar esto después del PID? → $0/mes, VM propia, `docker compose up`.
   - ¿Cómo sé que el sistema es confiable? → quality gates CI (coverage ≥ 70%), DoD nivel sistema en `marco/04-especificaciones.md`.
   - ¿Cómo se transfiere? → roadmap Fase 3 (2029): convenios, talleres, papers.

---

## 4. Gobierno y trazabilidad

- **Decisiones**: repositorio de ADRs (`docs/adr/0001`, `0002`) — toda decisión técnica relevante queda escrita con contexto, alternativa y consecuencia.
- **Requisitos → Objetivos → PPS**: matriz de trazabilidad en `marco/04-especificaciones.md` §5: cada requisito se liga a un objetivo del PID y a un entregable de PPS.
- **Cambios**: un cambio de arquitectura sigue el pipeline `caso de cambio → ADR → actualización de artefactos` (ver `decisiones/caso-postgresql-vs-sqlite.md` como ejemplo completo).
- **Calidad del proceso**: Spec-Driven Development (sin spec no hay código), planificación por backlog MoSCoW, seguimiento semanal en standup.

---

## 5. Próximos hitos visibles para interesados

| Fecha | Hito | Cómo se enteran |
|---|---|---|
| Jun 2026 | Contratos públicos (OpenAPI/AsyncAPI) + stack PostgreSQL en VM | PRs, este repo |
| Ago 2026 | Demo intermedia: anomalías + health score + dashboards | Presentación laboratorio |
| Oct 2026 | **MVP-0 operativo** + cierre PPS + informes | Informe PPS, demo GIDAS |
| Ene-Jun 2027 | MVP-1 validado (SUS > 75) + 3 papers base | Publicaciones, repo |
| 2027–2030 | Etapas E1/E2/E3 del PID | Informes PID, papers, conferencias |
| 2029–2030 | Transferencia: 2+ laboratorios adoptantes | Convenios, talleres |

---

## 6. Cómo participar

- **Adoptar**: seguir `roadmap/roadmap-producto.md` Fase 3, contactar dirección GIDAS.
- **Contribuir**: repo público, issues, specs vivas, licencia Apache-2.0.
- **Aprender**: talleres de formación RRHH (2029) y materiales del marco conceptual.
- **Difundir**: paper de divulgación del proyecto (`papers/divulgacion-intellops/articulo.md`).

---

*Documento vivo. Se actualiza en cada hito de fase y ante cambios de alcance aprobados por el coordinador.*