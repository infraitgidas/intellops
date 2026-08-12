# Informe de Avance 1 — RomeKai (Romeo L. Monfroglio)

> **Rol**: Arquitecto de datos / Investigador de métricas RUM
> **Período**: 20 — 24 de julio de 2026
> **Commits**: 4 (2 propios + 1 merge + 1 fix de merge)
> **Documentos generados**: 4 (3 PDFs + 1 PDF de explicación)

---

## 1. Actividades de Investigación

### 1.1. Selección de Métricas RUM para el MVP
Documento en `docs/research/Estrategia de Observabilidad Elección de métricas fundamentales para el MVP.pdf` (216 líneas extraídas):

**Marco conceptual**: Define la necesidad de la **observabilidad centrada en el usuario**, argumentando que el monitoreo tradicional de servidores es insuficiente porque:
- Un servidor puede responder en 40ms pero el navegador del usuario tardar segundos en renderizar
- Las métricas de servidor no detectan fricciones de UX
- La correlación frontend-backend es necesaria para un diagnóstico completo

**Espectro de 10 métricas analizadas** con un enfoque innovador de **"traducción psicológica"** que conecta el valor técnico con la percepción humana:

| # | Métrica | Dato técnico | Frustración que previene |
|---|---------|-------------|--------------------------|
| 1 | **LCP** | Largest Contentful Paint | Ansiedad de pantalla incompleta |
| 2 | **INP** | Interaction to Next Paint | "Clic muerto", interfaz congelada |
| 3 | **CLS** | Cumulative Layout Shift | Clics accidentales por saltos de layout |
| 4 | **JS Exception Rate** | Tasa de errores JavaScript | Botones inertes, flujos rotos silenciosos |
| 5 | **XHR/Fetch Latency** | Latencia de peticiones asíncronas | Spinners infinitos, limbo transaccional |
| 6 | **TTFB** | Time to First Byte | Pantalla blanca, "no carga nada" |
| 7 | **FCP** | First Contentful Paint | Ceguera inicial del usuario |
| 8 | **Long Tasks** | Tareas largas en hilo principal | Tartamudeo al scrollear, jank |
| 9 | **Rage Clicks** | Clics repetitivos por frustración | Hostilidad de la interfaz |
| 10 | **Crash-Free Sessions** | Sesiones sin caídas | Pérdida de trabajo no guardado |

**Recomendación estratégica para MVP — 5 métricas**:

| Prioridad | Métrica | Por qué para el MVP |
|-----------|---------|---------------------|
| 1 | **TTFB** | Número exacto del navegador, fácil de trazar línea base |
| 2 | **FCP** | Primer señal visual, dato limpio para ML |
| 3 | **XHR/Fetch Latency** | Mide directamente la comunicación con backend |
| 4 | **JS Exception Rate** | Error binario (pasó/no pasó), evita falsas alarmas |
| 5 | **Rage Clicks** | Fácil de implementar, traduce frustración a número |

**Criterio de selección**: Simplicidad técnica + calidad de datos para ML + viabilidad de implementación en 200h de PS.

---

## 2. Actividades de Análisis y Diseño de Software

### 2.1. Modelo de Datos — Diagrama Entidad-Relación V1
Primera versión del modelo de datos (`docs/der/DER intellops V1.pdf` + `Explicacion DER V1.pdf`):

**3 dominios, 8 tablas**:

**Dominio de Gestión de Usuarios:**
- `LAB_USER` — identidad de investigadores/administradores (user_id UUID, name, email, role, created_at)
- `USER_FAVORITE` — dashboards personalizados por usuario (favorite_id, user_id FK, metric_type, default_time_window)

**Dominio de Telemetría Frontend (RUM):**
- `USER_SESSION` — contexto de cada visita (session_id UUID, user_id FK nullable, ip_address, user_agent, os_version, start_timestamp)
- `RUM_METRIC` — tabla de series temporales (metric_id UUID, session_id FK, metric_type, value float, timestamp)
- `JS_EXCEPTION` — almacenamiento de errores separado de métricas rápidas (error_id UUID, session_id FK, error_type, message text, stack_trace text, timestamp)

**Dominio de IA y Alertas:**
- `ML_MODEL` — meta-información de modelos (model_id int, name, target_metric, version, last_trained_at)
- `ANOMALY` — anomalías detectadas (anomaly_id UUID, metric_id FK, model_id FK, expected_value, actual_value, severity_score, timestamp)
- `ALERT` — registro de notificaciones (alert_id UUID, anomaly_id FK, channel, status, sent_at)

### 2.2. Evolución a V1.2 — Soporte Multi-Tenant y MLOps
Segunda versión (`docs/der/DER intellops v1.2.pdf` + `Explicacion DER v1.2.pdf`) con mejoras significativas:

| Área | Cambio V1 → V1.2 | Justificación técnica |
|------|------------------|----------------------|
| **Multi-proyecto** | Nueva tabla `APPLICATION` + `app_id` en `USER_SESSION` | Soporte para monitorear N aplicaciones (Portal GIDAS, Dashboard Admin, Web Pública) sin mezclar datos |
| **Sesiones** | `end_timestamp` + `duration_ms` en `USER_SESSION` | Cálculo preciso de duración de visita sin depender de timestamps |
| **Métricas RUM** | `unit`, `page_url`, `metadata` (JSONB) en `RUM_METRIC` | JSONB permite flexibilidad sin alterar esquema; `page_url` da contexto de ubicación |
| **Errores** | `metric_id` opcional en `JS_EXCEPTION` | Permite rastrear si un error JS causó una métrica anómala |
| **MLOps** | `model_id` de INT a UUID + `status` + `hyperparameters` (JSONB) | UUID evita colisiones cross-máquina; `hyperparameters` es vital para reproducibilidad científica |
| **Anomalías** | `confidence_score` en `ANOMALY` | No basta decir "es anómalo", hay que decir con qué seguridad (98% vs 55%) |
| **Alertas** | `recipient` + `message` en `ALERT` | Registro histórico de a quién y qué se le notificó |
| **Usuarios** | `is_active` + `last_login` en `LAB_USER` | Borrado lógico + auditoría de acceso |
| **Nomenclatura** | `USER_FAVORITE` → `USER_FAVORITE_METRIC` | Nombre auto-explicativo |

---

## 3. Contribuciones a la Ingeniería de Software

### 3.1. Gestión de Versiones (SCM)
- Merge management: gestionó el merge de la rama `docs/diagrama-der` mediante PR #5

### 3.2. Gestión de Conocimiento
- **Diccionario de datos**: documentación detallada de cada tabla, campo, tipo y justificación
- **Documento de evolución**: explicación clara de los cambios V1→V1.2 con justificación técnica de cada modificación
- **Marco conceptual de métricas**: conexión entre métricas técnicas y percepción de usuario (traducción psicológica)

### 3.3. Diseño de Datos
- Diseño optimizado para **escritura masiva** (RUM_METRIC como tabla angosta de series temporales)
- Separación de **datos rápidos** (RUM_METRIC) de **datos pesados** (JS_EXCEPTION)
- Soporte para **evolución del esquema** mediante JSONB sin migraciones disruptivas
- Preparación para **MLOps** con metadatos de modelos, hiperparámetros y confidence scoring

---

## 4. Entregables

| # | Entregable | Tipo | Detalle |
|---|-----------|------|---------|
| 1 | `docs/research/Estrategia de Observabilidad Elección de métricas fundamentales para el MVP.pdf` | Documento de investigación | 10 métricas analizadas, 5 recomendadas para MVP |
| 2 | `docs/der/DER intellops V1.pdf` | Diagrama Entidad-Relación | Modelo de datos base (8 tablas, 3 dominios) |
| 3 | `docs/der/Explicacion DER V1.pdf` | Diccionario de datos | Documentación detallada de tablas, campos y justificación |
| 4 | `docs/der/DER intellops v1.2.pdf` | Diagrama Entidad-Relación | Modelo evolucionado con multi-tenant y MLOps |
| 5 | `docs/der/Explicacion DER v1.2.pdf` | Documento de evolución | Análisis de cambios V1→V1.2 con justificaciones |

---

## 5. Tiempo de Dedicación Estimado

| Actividad | Horas estimadas |
|-----------|----------------|
| Investigación de métricas RUM — lectura de documentación técnica (Web Vitals, W3C, OTel) | 8 |
| Redacción del documento de métricas — análisis de 10 métricas + traducción psicológica + selección MVP | 10 |
| Diseño del DER V1 — identificación de entidades, atributos, relaciones, normalización | 8 |
| Redacción del diccionario de datos V1 — documentación de cada tabla y campo | 4 |
| Evolución a DER V1.2 — análisis de multi-tenant, MLOps, mejoras de esquema | 6 |
| Redacción del documento de evolución V1→V1.2 | 3 |
| Reuniones de equipo y revisión con coordinador | 3 |
| **Total estimado** | **~42 horas** |

> **Nota**: El tiempo incluye investigación técnica, diseño, redacción y revisiones. No incluye aprendizaje de modelado de datos ni herramientas de diagramación.

---

*IntellOps — Informe de Avance 1 · 2026-07-30*
