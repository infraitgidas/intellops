# Gestión del Proyecto IntellOps

> **Directorio de gestión, planeación y gobernanza técnica del proyecto IntellOps**
> Sistema de Observabilidad Predictiva UX-Céntrica · GIDAS · UTN FrLP · InfraIT
> Enmarcado en el PID "Observabilidad de Infraestructura IT en la era de Producción de Software asistido por IA"

**Rama**: `gestionProyecto`
**Última actualización**: 2026-09-11

---

## ¿Qué es este directorio?

Este es el **centro de comando del proyecto**: contiene el marco conceptual e ingenieril de IntellOps
(objetivo → análisis → diseño → especificaciones), el backlog de producto priorizado, el análisis de
acoplamiento del equipo PPS 2026 y la documentación de referencia del PID institucional.

Es la fuente de verdad para **decisiones de gestión** y el punto de entrada para cualquier persona
(coordinador, colaboradores, dirección GIDAS) que necesite entender *qué es IntellOps, qué se está
construyendo y cómo encaja cada pieza*.

---

## Estructura del Directorio

```
gestionProyecto/
├── README.md                 ← Este índice maestro (también conocido como README.md)
├── marco/                    ← MARCO CONCEPTUAL (documentos 01-04)
│   ├── 01-objetivo.md        ←   Objetivo macro, tesis diferencial, KPIs
│   ├── 02-analisis.md        ←   Análisis sistémico, problema, stakeholders, mercado
│   ├── 03-diseno.md          ←   Arquitectura de capas, C4, módulos, ADRs
│   └── 04-especificaciones.md←   Requisitos funcionales/No funcionales, contratos
├── objetivo-alcance.md       ← VISIÓN CONSOLIDADA: qué/por qué/alcance/qué no — punto de entrada
├── backlog/
│   └── backlog.md            ← Backlog de producto priorizado (MoSCoW, épicas E01-E12)
├── diagramas/
│   ├── diagrama-actividades.puml       ← Diagrama de actividades de desarrollo del MVP (fuente)
│   ├── diagrama-actividades.png        ←   renderizado
│   ├── diagrama-macro-actividades.puml ← Diagrama MACRO: actividades de TODO el proyecto 2026-2030 (fuente)
│   ├── diagrama-macro-actividades.png  ←   renderizado
│   ├── diagrama-modulos-paquetes.puml  ← MÓDULOS Y PAQUETES: visión completa multi-capa (fuente)
│   └── diagrama-modulos-paquetes.png   ←   renderizado
├── audiencias/               ← DOCUMENTOS POR AUDIENCIA (docs vivas)
│   ├── interesados.md        ←   Para dirección/GIDAS/UTN: qué es, aporte, próximos hitos
│   ├── negocio.md            ←   Para decisores/adoptantes: propuesta de valor, costo, ROI
│   └── desarrolladores.md    ←   Para contributors/adoptantes técnicos: stack, contratos, DoD
├── roadmap/                  ← ROADMAPS
│   ├── roadmap-producto.md   ←   Roadmap completo del producto (2026→2030, alineado al PID)
│   └── roadmap-mvp-pps.md    ←   Roadmap del MVP mapeado a las 3 PPS 2026 (Federico/Romeo/Santiago)
├── decisiones/
│   └── caso-postgresql-vs-sqlite.md  ← Análisis de caso del cambio SQLite→PostgreSQL (pre-ADR-0002)
├── equipo/
│   └── analisis-pps-acoplamiento.md  ← Verificación de planes PPS 2026 + cambios propuestos
└── pid/
    └── resumen-pid.md        ← Síntesis del PID institucional (fuente: PID/Nahuel - Proyecto.pdf)
```

---

## Orden de Lectura Recomendado

| Paso | Documento | Para quién | Por qué |
|---|---|---|---|
| 1 | `pid/resumen-pid.md` | Todos | El marco institucional que da origen al proyecto |
| 2 | `marco/01-objetivo.md` | Todos | Define QUÉ es IntellOps y su valor diferencial |
| 3 | `marco/02-analisis.md` | Coordinación / dirección | El POR QUÉ sistémico, de negocio y de mercado |
| 4 | `marco/03-diseno.md` | Colaboradores / coordinación | El CÓMO: arquitectura y módulos |
| 5 | `marco/04-especificaciones.md` | Colaboradores | Los requisitos verificables (contrato) |
| 6 | `equipo/analisis-pps-acoplamiento.md` | Colaboradores PPS | Dónde encaja cada uno y qué cambiar |
| 7 | `backlog/backlog.md` | Todos | Qué se construye y en qué orden |

---

## Estado de los Documentos

| Documento | Versión | Estado | Revisado por |
|---|---|---|---|
| `objetivo-alcance.md` | 1.0 | **Publicado** | Coordinación 2026-09-11 |
| `marco/01-objetivo.md` | 1.0 | Publicado | Coordinación 2026-09-11 |
| `marco/02-analisis.md` | 1.1 | Publicado (+PostgreSQL ADR-0002) | Coordinación 2026-09-11 |
| `marco/03-diseno.md` | 1.1 | Publicado (+PostgreSQL ADR-0002) | Coordinación 2026-09-11 |
| `marco/04-especificaciones.md` | 1.2 | Publicado (DoD por módulo + gates §7, +PostgreSQL ADR-0002) | Coordinación 2026-09-11 |
| `backlog/backlog.md` | 1.1 | Publicado (planning poker + PostgreSQL, EP08) | Equipo 2026-09-11 |
| `diagramas/diagrama-actividades.*` | 1.0 | Generado | Coordinación 2026-09-11 |
| `diagramas/diagrama-macro-actividades.*` | 1.0 | Generado (2026→2030) | Coordinación 2026-09-11 |
| `diagramas/diagrama-modulos-paquetes.*` | 1.0 | Generado (C4) | Coordinación 2026-09-11 |
| `audiencias/*` | 1.0 | Publicado (3 audiencias) | Coordinación 2026-09-11 |
| `roadmap/roadmap-producto.md` | 1.0 | Publicado (2026→2030) | Coordinación 2026-09-11 |
| `roadmap/roadmap-mvp-pps.md` | 1.0 | Publicado (MVP→PPS) | Coordinación 2026-09-11 |
| `equipo/analisis-pps-acoplamiento.md` | 1.0 | Publicado | Coordinación 2026-09-11 |
| `pid/resumen-pid.md` | 1.0 | Publicado | Coordinación 2026-09-11 |

---

## Relación con el resto del repositorio

| Ruta | Rol | Relación con este directorio |
|---|---|---|
| `PID/` | Formulario oficial del PID (PDF) | Fuente primaria → sintetizado en `pid/resumen-pid.md` |
| `RRHH/` | Planes PPS oficiales de los colaboradores (DOCX/PDF) | Analizados y acoplados en `equipo/analisis-pps-acoplamiento.md` |
| `docs/adr/` | Decisiones de arquitectura (ADR) | Referenciadas en `marco/03-diseno.md` |
| `docs/research/` | Investigación del estado del arte | Fundamentan `marco/02-analisis.md` |
| `docs/brief-v2.md` | Brief redefinido del proyecto | Base técnica de `marco/` |
| `roadmap/roadmap-mvp-pps.md` | Plan PPS 2026 por contributor | Alineado con las PPS 2026 |
| `pid/resumen-pid.md` | Identidad institucional del PID | Marco de coherencia del proyecto |
| `openspec/specs/**` | Specs SDD detalladas | Nivel de detalle debajo de `marco/04` |

---

## Próximos Pasos (plan de acción)

- [ ] **Taller de alineación** con los 3 colaboradores: presentar marco + diagrama de actividades
- [ ] Actualizar planes PPS según `equipo/analisis-pps-acoplamiento.md`
- [ ] **Planning poker** sobre `backlog/backlog.md`
- [ ] Publicar contratos de datos compartidos (eventos seguridad, anomalías, health score)
- [ ] Revisión y aprobación del marco por dirección GIDAS

---

*Documento vivo. La estructura y los estados se actualizan en cada ciclo de gestión.*