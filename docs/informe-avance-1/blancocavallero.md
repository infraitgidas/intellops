# Informe de Avance 1 — BlancoCavallero (Federico Blanco Cavallero)

> **Rol**: Analista de negocio / Gestor de configuración
> **Período**: 17 — 25 de julio de 2026
> **Commits**: 11 (9 propios + 1 merge + 1 fix)
> **Archivos modificados**: 15

---

## 1. Actividades de Investigación

### 1.1. Análisis de Caso de Negocio
Documento en `docs/business/Análisis de Caso de NegocioV2.pdf` que describe:
- Problema de negocio que resuelve IntellOps
- Propuesta de valor para el laboratorio GIDAS
- Análisis de viabilidad y retorno de inversión
- Modelo de negocio y sostenibilidad del proyecto

### 1.2. Convención de Commits y Estándares de Contribución
Creación en dos iteraciones de `CONTRIBUTING.md` (112 líneas):
- Definición del formato de Conventional Commits adaptado al proyecto
- Estructura de commits: `tipo(alcance): descripción`
- Flujo de trabajo con ramas (main, develop, features)
- Guía para code review y merge requests
- Estándares de código y documentación

> **Nota**: Este documento es la base de la gestión de cambios del proyecto. Su creación demuestra comprensión de la importancia de la estandarización en equipos multidisciplinarios.

---

## 2. Actividades de Análisis y Diseño de Software

### 2.1. Especificación de Historias de Usuario
Dos versiones del documento en `docs/business/`:
- **V1** (`Especificación de Historias de Usuario.pdf`): primera versión con las HU identificadas
- **V1.2** (`Especificación de Historias de Usuario v1.2.pdf`): versión corregida incorporando feedback

Las HU conectan la investigación técnica con los requerimientos funcionales del producto.

### 2.2. Documentación de RRHH
Actualización de documentos administrativos:
- `Cronograma_IntellOps_Blanco_Cavallero_v3.docx` y `.pdf` — Cronograma personal de actividades
- `Solicitud_Inicio_IntellOps_Blanco_Cavallero_v3.pdf` — Solicitud formal de inicio de PS

---

## 3. Contribuciones a la Ingeniería de Software

### 3.1. Gestión de Versiones (SCM)
- **CONTRIBUTING.md**: estableció las reglas de conventional commits, flujo de ramas y estándares de PR para todo el equipo
- **Merge management**: gestionó el merge de la rama `docs/HU` mediante PR #4

### 3.2. Gestión de Configuración y CI/CD
Realizó **3 fixes consecutivos** al pipeline de CI que estaba roto:

| Commit | Archivo | Problema | Solución |
|--------|---------|----------|----------|
| `21e5eb1` | `src/api/main.py` | Descripción incorrecta en FastAPI | Corrección de metadata de la app |
| `7498f64` | `.github/workflows/ci.yml` | Pipeline CI fallando | Ajuste de steps y dependencias |
| `dd93246` | `.github/workflows/ci.yml`, `pyproject.toml`, `src/api/__init__.py`, `tests/test_health.py` | Health check no pasaba | Fix completo del endpoint `/health` + test |

### 3.3. Gestión del Conocimiento
- **Minuta de reunión 20-07-2026** (`docs/meetings/20-07-2026`, 35 líneas): registro de la reunión del equipo con decisiones, asignaciones y próximos pasos
- **Historias de Usuario**: documentación de requerimientos accesible para todo el equipo, cerrando la brecha entre investigación técnica y desarrollo

### 3.4. Resolución de Incidencias Técnicas
Los 3 commits de fix demuestran capacidad de diagnóstico y resolución de problemas en un stack que no configuró inicialmente (FastAPI + pytest + GitHub Actions).

---

## 4. Entregables

| # | Entregable | Tipo | Detalle |
|---|-----------|------|---------|
| 1 | `CONTRIBUTING.md` | Guía de contribución | 112 líneas — convención de commits, flujo, estándares |
| 2 | `docs/business/Análisis de Caso de NegocioV2.pdf` | Documento de negocio | Análisis de viabilidad y propuesta de valor |
| 3 | `docs/business/Especificación de Historias de Usuario.pdf` | Especificación funcional | HU versión base |
| 4 | `docs/business/Especificación de Historias de Usuario v1.2.pdf` | Especificación funcional | HU corregidas y actualizadas |
| 5 | `RRHH/Federico Cavallero/Cronograma_IntellOps_Blanco_Cavallero_v3.docx` | Documento administrativo | Cronograma personal |
| 6 | `RRHH/Federico Cavallero/Cronograma_IntellOps_Blanco_Cavallero_v3.pdf` | Documento administrativo | Cronograma personal (PDF) |
| 7 | `RRHH/Federico Cavallero/Solicitud_Inicio_IntellOps_Blanco_Cavallero_v3.pdf` | Documento administrativo | Solicitud de inicio |
| 8 | `docs/meetings/20-07-2026` | Minuta de reunión | 35 líneas |
| 9 | `.github/workflows/ci.yml` | Pipeline CI | Fix de CI |
| 10 | `src/api/main.py` | Código | Fix de health check |
| 11 | `src/api/__init__.py` | Código | Archivo de módulo |
| 12 | `pyproject.toml` | Configuración | Ajuste de config |
| 13 | `tests/test_health.py` | Tests | Fix de test de health |

---

## 5. Tiempo de Dedicación Estimado

| Actividad | Horas estimadas |
|-----------|----------------|
| CONTRIBUTING.md — investigación de estándares + redacción + corrección | 6 |
| Análisis de Caso de Negocio — investigación + análisis + documento | 12 |
| Especificación de Historias de Usuario V1 — identificación + redacción | 8 |
| Especificación de Historias de Usuario V1.2 — revisión + corrección | 4 |
| Documentación RRHH — actualización de cronograma y solicitud | 4 |
| Diagnóstico y fixes de CI — 3 iteraciones sobre CI + FastAPI | 6 |
| Minuta de reunión 20-07-2026 | 2 |
| Reuniones de equipo y comunicación asíncrona | 4 |
| **Total estimado** | **~46 horas** |

> **Nota**: El tiempo incluye investigación, redacción, revisiones y correcciones. No incluye tiempo de aprendizaje de tecnologías nuevas.

---

*IntellOps — Informe de Avance 1 · 2026-07-30*
