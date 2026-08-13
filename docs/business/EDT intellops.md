# Plan de Desarrollo y EDT — Sistema de Monitoreo RUM + IA

## Equipo

| Integrante | Responsabilidad principal |
|---|---|
| **Santiago** | Core Backend / Datos / Seguridad |
| **Federico** | Telemetría / RUM / Procesamiento |
| **Romeo** | Inteligencia Artificial / Anomalías / Alertas |

---

# 1. Estrategia general de desarrollo

El proyecto se organizará en **8 sprints de 2 semanas**, comenzando el **24 de agosto de 2026**.

La estrategia busca concentrar los primeros sprints en **backend, arquitectura de datos, ingesta, procesamiento e inteligencia artificial**, dejando el frontend para la segunda mitad del proyecto, cuando las APIs y la lógica de negocio ya estén estabilizadas.

### Distribución temporal

| Sprint | Fechas | Objetivo principal |
|---|---|---|
| **S1** | 24/08 – 06/09 | Arquitectura + infraestructura + contratos |
| **S2** | 07/09 – 20/09 | Backend core + ingesta RUM |
| **S3** | 21/09 – 04/10 | Sesiones + métricas + procesamiento |
| **S4** | 05/10 – 18/10 | ML + modelos + entrenamiento |
| **S5** | 19/10 – 01/11 | Anomalías + alertas + hardening backend |
| **S6** | 02/11 – 15/11 | Integración backend completa + frontend base |
| **S7** | 16/11 – 29/11 | Frontend completo |
| **S8** | 30/11 – 13/12 | Integración final + testing + deploy |

### Filosofía de trabajo

**S1–S5:** Backend + IA  
**S6:** Integración + comienzo frontend  
**S7–S8:** Frontend + integración + QA

El principio fundamental será:

> **Cada módulo tiene un único responsable técnico.**

Los demás integrantes pueden consumir ese módulo mediante interfaces y contratos definidos, pero no deberían modificarlo salvo que exista una necesidad explícita.

---

# 2. División definitiva de responsabilidades

## 2.1. Santiago — Core Backend / Datos / Seguridad

Santiago será responsable de:

- Base de datos.
- `APPLICATION`.
- `LAB_USER`.
- `USER_FAVORITE_METRIC`.
- `USER_SESSION`.
- Autenticación.
- Autorización.
- Gestión de usuarios.
- Gestión de aplicaciones.
- Gestión de sesiones.
- API Core.
- Seguridad.
- Infraestructura backend.
- Performance del backend.

No será responsable de la lógica de Machine Learning.

---

## 2.2. Federico — Telemetría / RUM / Procesamiento

Federico será responsable de:

- `RUM_METRIC`.
- `JS_EXCEPTION`.
- Collector.
- SDK/agente de captura.
- Ingesta.
- Validación de eventos.
- Normalización.
- Procesamiento.
- Agregaciones.
- Pipelines.
- Dataset para ML.
- API de métricas.
- Procesamiento de datos.

No será responsable de implementar los algoritmos de Machine Learning.

---

## 2.3. Romeo — IA / Anomalías / Alertas

Romeo será responsable de:

- `ML_MODEL`.
- `ANOMALY`.
- `ALERT`.
- Preparación final de datos para ML.
- Feature engineering.
- Selección de modelos.
- Entrenamiento.
- Evaluación.
- Versionado.
- Inferencia.
- Detección de anomalías.
- Severity score.
- Confidence score.
- Sistema de alertas.
- Integración de alertas con los canales disponibles.

No será responsable de modificar la ingesta ni el Core Backend.

---

# 3. EDT General

```text
1. Gestión y arquitectura
   1.1 Requerimientos
   1.2 Arquitectura
   1.3 Modelo de datos
   1.4 Contratos API
   1.5 Infraestructura
   1.6 Repositorio y CI/CD

2. Backend Core
   2.1 Usuarios
   2.2 Autenticación
   2.3 Aplicaciones
   2.4 Sesiones
   2.5 Favoritos
   2.6 API Core

3. Telemetría
   3.1 Collector
   3.2 RUM
   3.3 JS Exceptions
   3.4 Ingesta
   3.5 Procesamiento
   3.6 Agregación
   3.7 API métricas

4. Inteligencia Artificial
   4.1 Preparación dataset
   4.2 Feature engineering
   4.3 Modelos
   4.4 Entrenamiento
   4.5 Evaluación
   4.6 Versionado
   4.7 Inferencia

5. Anomalías
   5.1 Detección
   5.2 Severidad
   5.3 Confianza
   5.4 Persistencia
   5.5 API

6. Alertas
   6.1 Reglas
   6.2 Canales
   6.3 Envío
   6.4 Reintentos
   6.5 Estado
   6.6 Historial

7. Frontend
   7.1 Arquitectura
   7.2 Login
   7.3 Dashboard
   7.4 Métricas
   7.5 Sesiones
   7.6 Anomalías
   7.7 Alertas
   7.8 Administración

8. Integración
   8.1 Backend
   8.2 RUM
   8.3 ML
   8.4 Frontend
   8.5 E2E

9. QA

10. Deploy

11. Documentación
```

---

# SPRINT 1 — 24/08 al 06/09
## Arquitectura e infraestructura

El objetivo del primer sprint será establecer una base técnica común. No se recomienda comenzar todavía con el desarrollo de funcionalidades grandes.

## Santiago — Arquitectura Backend

### 1.1. Diseño de backend

- Definir arquitectura de servicios.
- Definir estructura de módulos.
- Definir responsabilidades de cada módulo.
- Definir estrategia de acceso a datos.
- Definir estrategia de autenticación.
- Definir manejo de errores.
- Definir logging.
- Definir configuración por ambiente.

### 1.2. Modelo de datos

Implementar inicialmente:

- `APPLICATION`.
- `LAB_USER`.
- `USER_FAVORITE_METRIC`.
- `USER_SESSION`.

Definir:

- PK.
- FK.
- Índices.
- Restricciones.
- Campos nullable.
- Timestamps.
- Tipos de datos.
- Convenciones de nombres.

### 1.3. Proyecto backend

- Crear proyecto.
- Configurar dependencias.
- Configurar variables de entorno.
- Configurar conexión a DB.
- Configurar migraciones.
- Configurar logging.
- Configurar manejo global de excepciones.

### Entregable de Santiago — S1

- Arquitectura backend documentada.
- Modelo de datos inicial.
- Proyecto backend compilando/ejecutando.
- Base de datos conectada.
- Migraciones funcionales.

---

## Federico — Arquitectura de Telemetría

### 1.4. Diseño de ingesta

Definir:

- Estructura de un evento RUM.
- Estructura de un evento de excepción.
- Esquema de validación.
- Timestamp.
- Identificador de sesión.
- Identificador de aplicación.
- Formato de metadata.

Diseñar:

```text
Application
     ↓
Collector
     ↓
API Ingestion
     ↓
Validation
     ↓
Storage
```

### 1.5. Diseño de métricas

Definir:

- Tipos de métricas.
- Unidades.
- Nomenclatura.
- Payload estándar.
- Eventos obligatorios.
- Eventos opcionales.

Diseñar contrato para `RUM_METRIC`.

### 1.6. Diseño de exceptions

Definir contrato de `JS_EXCEPTION`, incluyendo:

- `error_type`.
- `message`.
- `stack_trace`.
- `session_id`.
- `metric_id`.
- `timestamp`.

### Entregable de Federico — S1

- Contrato de eventos RUM.
- Contrato de excepciones.
- Diseño del collector.
- Esquema de validación.

---

## Romeo — Arquitectura de IA

### 1.7. Definición del módulo ML

Definir:

- Problema de detección.
- Variable objetivo.
- Inputs del modelo.
- Outputs del modelo.
- Frecuencia de entrenamiento.
- Frecuencia de inferencia.
- Métricas de evaluación.
- Estrategia de versionado.

### 1.8. Diseño de entidades ML

Diseñar:

- `ML_MODEL`.
- `ANOMALY`.
- `ALERT`.

### 1.9. Pipeline conceptual

```text
RUM_METRIC
     ↓
Feature Engineering
     ↓
Model
     ↓
Prediction
     ↓
Anomaly
     ↓
Alert
```

### Entregable de Romeo — S1

- Arquitectura del módulo IA.
- Diseño de entidades ML.
- Pipeline conceptual.
- Contrato de entrada/salida del modelo.

---

## Entregable global S1

Al finalizar el sprint debe existir:

- Arquitectura definida.
- DB definida.
- Contratos API definidos.
- Contratos de telemetría definidos.
- Arquitectura ML definida.
- Repositorio.
- CI.
- Ambiente de desarrollo.
- Documentación técnica inicial.

**No se inicia todavía el frontend.**

---

# SPRINT 2 — 07/09 al 20/09
## Backend Core + Ingesta

## Santiago — Core Backend

### 2.1. Usuarios

- Crear modelo `LAB_USER`.
- Crear acceso a datos.
- Crear CRUD.
- Validaciones.
- Roles.
- `is_active`.

### 2.2. Autenticación

- Login.
- Logout.
- Hash de contraseñas.
- Gestión de sesión/token.
- Middleware de autenticación.
- Manejo de credenciales inválidas.

### 2.3. Applications

- CRUD de `APPLICATION`.
- Validación de permisos.
- Endpoints.
- Asociación aplicación-usuario cuando corresponda.

### 2.4. API

Primera versión de:

```text
POST /auth/login
POST /auth/logout

GET /users
GET /users/{id}

GET /applications
POST /applications
GET /applications/{id}
PUT /applications/{id}
DELETE /applications/{id}
```

### Entregable

- Autenticación funcional.
- Usuarios funcionales.
- Aplicaciones funcionales.
- API Core operativa.

---

## Federico — Collector + RUM

### 2.5. Collector

Implementar:

- Endpoint de ingesta.
- Validación.
- Serialización.
- Manejo de errores.
- Persistencia.
- Logs de eventos inválidos.

### 2.6. RUM

Implementar `RUM_METRIC`.

Pipeline:

```text
POST /telemetry/metrics
        ↓
Validation
        ↓
Normalization
        ↓
Database
```

### 2.7. Exceptions

Implementar:

```text
POST /telemetry/exceptions
```

Persistencia de `JS_EXCEPTION`.

### Entregable

Debe ser posible recibir y persistir métricas y excepciones desde una aplicación monitoreada.

---

## Romeo — Fundamentos de ML

Todavía no se desarrolla el modelo definitivo.

### 2.8. Dataset inicial

- Generar dataset sintético si no existe suficiente información real.
- Crear notebook/proyecto reproducible.
- Realizar exploración estadística.
- Identificar outliers.
- Analizar distribuciones.
- Analizar correlaciones.

### 2.9. Evaluación preliminar de algoritmos

Evaluar alternativas como:

- Métodos estadísticos.
- Thresholds dinámicos.
- Isolation Forest.
- Modelos de series temporales.
- Enfoques híbridos.

### Entregable

- Dataset inicial.
- Análisis exploratorio.
- Comparación preliminar de enfoques.

---

# SPRINT 3 — 21/09 al 04/10
## Sesiones + procesamiento

## Santiago — Sessions + Favorites

### 3.1. `USER_SESSION`

Implementar:

- Creación de sesión.
- Asociación con aplicación.
- Asociación opcional con usuario.
- IP.
- User Agent.
- Sistema operativo.
- `start_timestamp`.
- `end_timestamp`.
- Cálculo de duración.

Endpoints:

```text
POST /sessions
POST /sessions/{id}/finish

GET /sessions
GET /sessions/{id}
```

### 3.2. `USER_FAVORITE_METRIC`

Implementar:

- Agregar favorito.
- Eliminar favorito.
- Consultar favoritos.
- Configurar ventana temporal.

### Entregable

Sesiones y favoritos completamente funcionales vía API.

---

## Federico — Procesamiento de datos

### 3.3. Normalización

- Convertir unidades.
- Validar timestamps.
- Normalizar nombres de métricas.
- Eliminar o marcar payloads inválidos.

### 3.4. Agregaciones

Por ejemplo:

```text
application
metric_type
time_window
```

Calcular:

- Promedio.
- Mínimo.
- Máximo.
- Percentiles.
- Cantidad de eventos.
- Tasa de error.

### 3.5. API de métricas

```text
GET /metrics
GET /metrics/{type}
GET /metrics/timeseries
GET /exceptions
```

### 3.6. Dataset para ML

Generar:

```text
timestamp
metric_type
value
application
session_count
error_count
...
```

### Entregable

Pipeline de datos capaz de transformar eventos crudos en datos analizados y utilizables por ML.

---

## Romeo — Feature Engineering

### 3.7. Variables temporales

Definir:

- Hora.
- Día.
- Día de semana.
- Ventanas temporales.

### 3.8. Features estadísticas

Implementar:

- Rolling average.
- Desviación estándar.
- Percentiles.
- Frecuencia.
- Variación porcentual.
- Tendencia.
- Valores históricos.

### 3.9. Pipeline

```text
Raw Metrics
     ↓
Cleaning
     ↓
Features
     ↓
Dataset ML
```

### Entregable

Pipeline reproducible desde dataset procesado hasta features listas para modelos.

---

# SPRINT 4 — 05/10 al 18/10
## Inteligencia Artificial

## Santiago — Hardening Backend

### 4.1. Seguridad

- Autorización.
- Validaciones.
- Protección de endpoints.
- Control de permisos.

### 4.2. Performance

- Revisar queries.
- Agregar índices.
- Revisar paginación.
- Optimizar endpoints.
- Analizar consultas costosas.

### 4.3. API

- Completar contratos.
- Estandarizar errores.
- Mejorar documentación.

### Entregable

Core Backend estable para el consumo del pipeline de ML.

---

## Federico — Pipeline de datos

### 4.4. Calidad de datos

- Detectar datos faltantes.
- Tratar outliers.
- Estandarizar intervalos temporales.
- Automatizar generación del dataset.
- Revisar consistencia.

### 4.5. Integración con ML

Preparar interfaces para que Romeo consuma los datos sin acoplamiento directo a la implementación del pipeline de ingesta.

### Entregable

Pipeline estable desde datos almacenados hasta dataset de entrenamiento/inferencia.

---

## Romeo — Entrenamiento del modelo

### 4.6. Entrenamiento

- Crear pipeline de entrenamiento.
- Preparar dataset.
- Separar train/test cuando corresponda.
- Entrenar modelos.
- Evaluar alternativas.

### 4.7. Evaluación

Analizar:

- Precision.
- Recall.
- False positives.
- False negatives.
- Confidence.

### 4.8. `ML_MODEL`

Persistir:

- Nombre.
- Versión.
- Target.
- Hyperparameters.
- Estado.
- Fecha de entrenamiento.

Flujo:

```text
MODEL
  v1
   ↓
training
   ↓
evaluation
   ↓
active
```

### Entregable

Primer modelo reproducible, evaluado y versionado.

---

# SPRINT 5 — 19/10 al 01/11
## Anomalías + Alertas + MVP Backend

Este sprint debe cerrar la primera versión funcional del backend y del núcleo de IA.

## Santiago — Persistencia y APIs ML

### 5.1. Modelo `ANOMALY`

- Crear entidad.
- Crear relaciones.
- Crear índices.
- Crear migraciones.
- Crear acceso a datos.

### 5.2. Modelo `ALERT`

- Crear entidad.
- Crear relaciones.
- Crear índices.
- Crear estados.
- Crear historial.

### 5.3. APIs

Crear endpoints para:

```text
/anomalies
/alerts
/models
```

### Entregable

Persistencia y APIs para el resultado del modelo.

---

## Federico — Pipeline de ejecución

### 5.4. Pipeline operacional

Implementar:

```text
Metric
 ↓
Aggregation
 ↓
Feature
 ↓
ML
```

### 5.5. Procesamiento

Evaluar si se necesita:

- Procesamiento batch.
- Procesamiento individual.
- Workers.
- Colas.
- Jobs programados.

### 5.6. Consistencia

- Validar idempotencia.
- Evitar procesamiento duplicado.
- Registrar errores.
- Registrar tiempos de procesamiento.

### Entregable

Pipeline completo y ejecutable desde la métrica hasta el modelo.

---

## Romeo — Anomaly Engine + Alert Engine

### 5.7. Detección de anomalías

Implementar:

```text
actual_value
expected_value
       ↓
difference
       ↓
severity
       ↓
confidence
```

Persistir `ANOMALY`.

### 5.8. Sistema de alertas

Implementar:

```text
ANOMALY
   ↓
Rule
   ↓
ALERT
   ↓
Channel
```

Estados:

```text
pending
sent
failed
retry
```

### 5.9. Abstracción de canales

Implementar:

```text
NotificationService
       ├── Email
       ├── Telegram
       └── WhatsApp
```

El sistema debe quedar desacoplado de un proveedor específico.

### Entregable

Sistema de anomalías y alertas funcional.

---

## MVP al finalizar S5

Debe ser posible ejecutar:

```text
Application
       ↓
Session
       ↓
RUM Metric
       ↓
Processing
       ↓
ML
       ↓
Anomaly
       ↓
Alert
```

Este será el **MVP técnico del backend + IA**.

---

# SPRINT 6 — 02/11 al 15/11
## Integración + comienzo del frontend

Recién en este sprint comienza formalmente el frontend.

## Santiago — Backend final

- Cerrar endpoints.
- Corregir inconsistencias.
- Completar documentación OpenAPI.
- Revisar permisos.
- Agregar paginación.
- Agregar filtros.
- Optimizar performance.
- Revisar seguridad.

### Entregable

Backend estable y consumible por frontend.

---

## Federico — Frontend base

### 6.1. Arquitectura

- Crear proyecto.
- Configurar routing.
- Configurar componentes.
- Configurar cliente HTTP.
- Configurar manejo de sesión.

### 6.2. Login

- Login.
- Logout.
- Protección de rutas.
- Manejo de tokens.
- Manejo de errores.

### 6.3. Layout

- Sidebar.
- Navbar.
- Navegación.
- Selector de aplicación.

### Entregable

Frontend base navegable y conectado al backend.

---

## Romeo — Integración ML

Validar pipeline completo:

- Métricas reales.
- Inferencia.
- Anomalías.
- Alertas.
- Thresholds.
- False positives.
- Performance.

Preparar endpoints de consumo frontend:

```text
/anomalies
/alerts
/models
```

### Entregable

Módulo IA listo para integrarse con la interfaz.

---

# SPRINT 7 — 16/11 al 29/11
## Frontend completo

## Santiago — Administración

Construir:

- Usuarios.
- Applications.
- Sessions.
- Permisos.
- Administración.
- Tablas.
- Filtros.
- Paginación.

---

## Federico — Dashboard principal

Construir:

- KPIs.
- Métricas.
- Gráficos.
- Series temporales.
- Filtros.
- Ventanas temporales.
- Favoritos.
- Detalle de aplicación.

Vista conceptual:

```text
Dashboard
 ├── Performance
 ├── Errors
 ├── Sessions
 ├── Anomalies
 └── Alerts
```

---

## Romeo — IA en frontend

Construir:

- Listado de anomalías.
- Severity.
- Confidence.
- Histórico.
- Alertas.
- Estado de alertas.
- Información de modelos.
- Presentación de resultados del modelo.

---

# SPRINT 8 — 30/11 al 13/12
## Integración final + QA + Deploy

Este sprint debe enfocarse principalmente en estabilización.

## Santiago — Backend QA

- Integration tests.
- Security tests.
- API tests.
- Performance.
- DB.
- Migrations.
- Recovery.
- Validación de permisos.

---

## Federico — Frontend QA

- Responsive.
- Manejo de errores.
- Loading states.
- Empty states.
- Navegación.
- Tests E2E.
- Accesibilidad básica.

---

## Romeo — ML QA

- Precisión.
- Estabilidad.
- False positives.
- Inferencia.
- Carga.
- Alertas.
- Retries.

---

## QA conjunto

Probar flujo end-to-end:

```text
User
 ↓
Login
 ↓
Application
 ↓
Session
 ↓
Metric
 ↓
Processing
 ↓
ML
 ↓
Anomaly
 ↓
Alert
 ↓
Dashboard
```

---

# 4. Dependencias entre los tres desarrolladores

## Santiago — Core Backend

```text
DB
 ↓
Models
 ↓
Auth
 ↓
Users
 ↓
Applications
 ↓
Sessions
 ↓
API Core
```

Santiago es el owner de esta cadena.

---

## Federico — Telemetría y procesamiento

```text
Collector
 ↓
RUM
 ↓
Exceptions
 ↓
Normalization
 ↓
Aggregation
 ↓
Dataset
```

Federico es el owner de esta cadena.

---

## Romeo — Inteligencia Artificial

```text
Dataset
 ↓
Features
 ↓
Model
 ↓
Prediction
 ↓
Anomaly
 ↓
Alert
```

Romeo es el owner de esta cadena.

---

# 5. Regla fundamental de ownership

Para minimizar conflictos de código y solapamiento:

| Módulo | Responsable |
|---|---|
| DB Core | **Santiago** |
| Auth | **Santiago** |
| Users | **Santiago** |
| Applications | **Santiago** |
| Sessions | **Santiago** |
| RUM | **Federico** |
| Exceptions | **Federico** |
| Processing | **Federico** |
| Aggregation | **Federico** |
| Dataset | **Federico** |
| ML | **Romeo** |
| Anomalies | **Romeo** |
| Alerts | **Romeo** |
| Frontend Admin | **Santiago** |
| Dashboard | **Federico** |
| IA UI | **Romeo** |

Los demás desarrolladores pueden consumir el módulo, definir contratos o aportar revisiones, pero el owner es quien realiza los cambios principales.

---

# 6. Contratos para evitar bloqueos

Un objetivo importante es que Romeo no quede bloqueado esperando a Federico, ni Federico esperando a Santiago.

Para ello se definirá un contrato de dataset en S1-S3.

Ejemplo:

```json
{
  "application_id": "...",
  "metric_type": "LCP",
  "timestamp": "...",
  "value": 1850,
  "session_count": 25,
  "error_count": 2
}
```

Federico produce datos con este formato.

Romeo puede desarrollar usando un dataset mock que respete exactamente el mismo contrato.

Así:

```text
DEV 2
real data ─────────┐
                   ├──→ ML
mock data ─────────┘
```

Los dos equipos pueden avanzar en paralelo.

---

# 7. Reglas de trabajo recomendadas

## Regla 1 — Un módulo, un owner

Cada módulo tiene un único responsable.

## Regla 2 — Contratos antes de integración

Antes de conectar dos módulos se define:

- Request.
- Response.
- Errores.
- Identificadores.
- Formato de datos.
- Versionado.

## Regla 3 — No modificar directamente el módulo de otro desarrollador

Primero se coordina mediante el contrato/API.

## Regla 4 — Pull Requests obligatorios

Todo cambio relevante debe pasar por:

```text
Feature branch
      ↓
Pull Request
      ↓
Code Review
      ↓
Merge
```

## Regla 5 — Frontend contra APIs estables

No se empieza a construir el dashboard completo hasta que los endpoints principales estén definidos y suficientemente estabilizados.

---

# 8. Reparto resumido por desarrollador

## SANTIAGO

```text
1. Arquitectura Backend
2. Base de Datos
3. Usuarios
4. Autenticación
5. Applications
6. Sessions
7. Favoritos
8. API Core
9. Seguridad
10. Performance
11. Frontend administrativo
12. Backend QA
```

## FEDERICO

```text
1. Telemetry Architecture
2. Collector
3. RUM Metrics
4. JS Exceptions
5. Ingestion
6. Normalization
7. Aggregation
8. Data Processing
9. Dataset ML
10. API Metrics
11. Dashboard
12. Frontend QA
```

## ROMEO

```text
1. ML Architecture
2. Dataset Analysis
3. Feature Engineering
4. Model Selection
5. Training
6. Evaluation
7. ML Model Management
8. Inference
9. Anomaly Detection
10. Severity / Confidence
11. Alerts
12. IA Frontend
13. ML QA
```

---

# 9. Estado esperado al finalizar cada sprint

| Sprint | Estado esperado |
|---|---|
| **S1** | Arquitectura y contratos definidos |
| **S2** | Backend core + ingesta funcionando |
| **S3** | Sesiones + procesamiento funcionando |
| **S4** | Primer modelo ML funcional |
| **S5** | Backend + ML + anomalías + alertas funcionando |
| **S6** | Sistema integrado + frontend iniciado |
| **S7** | Frontend funcional |
| **S8** | Sistema completo, probado y desplegable |

---

# 10. Resultado esperado de la estrategia

La arquitectura de trabajo queda organizada como tres pipelines principales:

```text
                  SANTIAGO
              CORE BACKEND
                  │
                  ▼
              API / DB
                  │
          ┌───────┴────────┐
          │                │
          ▼                ▼
       FEDERICO           ROMEO
      TELEMETRÍA            ML
          │                │
          │                │
          └───────┬────────┘
                  ▼
             INTEGRATION
                  │
                  ▼
               FRONTEND
```

La mayor parte del solapamiento se concentra únicamente en:

- definición inicial de contratos;
- integración;
- code review;
- QA;
- deploy.

El resto del desarrollo queda segmentado por dominio.

El objetivo es que los primeros cinco sprints generen el **producto técnico principal** —backend, procesamiento, IA, anomalías y alertas— y que los últimos tres sprints se utilicen para convertir ese núcleo en una aplicación completa, estable y fácil de presentar.
