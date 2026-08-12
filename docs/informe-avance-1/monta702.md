# Informe de Avance 1 — Monta702 (Santiago Montanari)

> **Rol**: Documentador de infraestructura / Soporte técnico
> **Período**: 21 — 29 de julio de 2026
> **Commits**: 9 (6 propios + 3 merges)
> **Documentos generados**: 6

---

## 1. Actividades de Investigación

### 1.1. Estructura de Carpetas del Proyecto
Investigación sobre la organización ideal de directorios para un proyecto de observabilidad con componentes de ML. Generó **3 versiones** del documento:

| Versión | Archivo | Estado |
|---------|---------|--------|
| V1 | `docs/infrastructure/Estructura-de-Carpetas.pdf` | Versión base inicial |
| V1.1 | `docs/infrastructure/Estructura-de-Carpetas.V1.pdf` | Versión con comentarios de revisión |
| V1.1.2 | `docs/infrastructure/Estructura-de-Carpetas-V1.1.2.pdf` | Versión final sin comentarios |

El proceso de versionado demuestra comprensión del ciclo de revisión y corrección de documentos técnicos.

### 1.2. Investigación de Base de Datos
Documento `docs/infrastructure/Investigacion-base-de-datos.pdf` que explora:
- Alternativas de bases de datos para el proyecto
- Consideraciones de almacenamiento para series temporales de RUM
- Integración con el modelo de datos propuesto

---

## 2. Actividades de Análisis y Diseño de Software

### 2.1. Diagrama C4 de Contenedores
Creación del `docs/infrastructure/Diagrama-C4.png` que representa la arquitectura de contenedores del sistema:

El diagrama C4 (Contexto-Contenedores-Componentes-Código) es el estándar de la industria para documentar arquitectura de software. Este diagrama cubre el nivel 2 (Contenedores), mostrando:
- Aplicaciones y servicios que componen el sistema
- Comunicación entre contenedores
- Tecnologías involucradas en cada contenedor

### 2.2. Documentación de Infraestructura
Organización y estructuración de la documentación de infraestructura del proyecto, estableciendo la base para que futuros contributors entiendan la disposición de componentes.

---

## 3. Contribuciones a la Ingeniería de Software

### 3.1. Gestión de Versiones (SCM)
- **3 merges gestionados**: PRs #1, #3 y #6 desde la rama `docs/actualizacion` hacia `develop`
- **Versionado de documentos**: implementó un esquema de versionado semántico para la documentación de infraestructura (V1 → V1.1 → V1.1.2), demostrando comprensión de la gestión de cambios sobre artefactos

### 3.2. Gestión del Conocimiento
- **Minuta de reunión 23-07-2026** (`docs/meetings/23-07-2026`, 30 líneas): registro detallado de la reunión del equipo incluyendo:
  - Temas discutidos y decisiones tomadas
  - Asignaciones de tareas y responsables
  - Próximos pasos y fechas compromiso
- **Documentación estructurada de infraestructura**: estableció un marco documental reusable para el área de infraestructura del proyecto

### 3.3. Gestión de Configuración
- **Estructura de directorios documentada**: la investigación y versionado de la estructura de carpetas sirve como guía de configuración del proyecto para nuevos contributors
- **Corrección de documentos**: identificó y eliminó comentarios de revisión en los documentos (commit `6bb5ef8`), asegurando que la documentación entregable esté limpia y profesional

---

## 4. Entregables

| # | Entregable | Tipo | Detalle |
|---|-----------|------|---------|
| 1 | `docs/infrastructure/Diagrama-C4.png` | Diagrama arquitectónico | Nivel 2 (Contenedores) de C4 |
| 2 | `docs/infrastructure/Estructura-de-Carpetas.pdf` | Documento técnico | Estructura base del proyecto |
| 3 | `docs/infrastructure/Estructura-de-Carpetas.V1.pdf` | Documento técnico | Versión con revisión |
| 4 | `docs/infrastructure/Estructura-de-Carpetas-V1.1.2.pdf` | Documento técnico | Versión final corregida |
| 5 | `docs/infrastructure/Investigacion-base-de-datos.pdf` | Documento de investigación | Análisis de alternativas de DB |
| 6 | `docs/meetings/23-07-2026` | Minuta de reunión | 30 líneas — registro de reunión |

---

## 5. Tiempo de Dedicación Estimado

| Actividad | Horas estimadas |
|-----------|----------------|
| Diagrama C4 — investigación de arquitectura + diseño + herramienta de diagramación | 6 |
| Estructura de carpetas V1 — investigación de organización de proyectos similares | 4 |
| Estructura de carpetas V1.1 — revisión + ajustes | 2 |
| Estructura de carpetas V1.1.2 — corrección final + limpieza de comentarios | 2 |
| Investigación de base de datos — lectura de documentación + análisis | 8 |
| Minuta de reunión 23-07-2026 | 2 |
| Gestión de merges (3 PRs) + resolución de conflictos | 3 |
| Reuniones de equipo y coordinación | 4 |
| **Total estimado** | **~31 horas** |

> **Nota**: El tiempo incluye investigación, diseño, redacción y revisiones.

---

*IntellOps — Informe de Avance 1 · 2026-07-30*
