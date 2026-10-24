# Especificación Detallada de Entregables
**Alumno:** Romeo Lorenzo Monfroglio (Leg. 31143)
**Práctica Profesional Supervisada:** V-06 — Módulo de Observabilidad con Detección de Anomalías (ML)
**Proyecto:** IntellOps — Sub-proyecto SP-2 · Laboratorio GIDAS · UTN FRLP
**Carga Horaria Aprobada:** 200 horas

A continuación se detallan los entregables formales de software y documentación que certifican el cumplimiento de los objetivos de la PS V-06, respetando la estructura de actividades y la carga horaria del Plan de Trabajo original. 

La arquitectura modular del MVP de IntellOps fomentó un esquema colaborativo donde el esfuerzo operativo se sincronizó mediante contratos e interfaces estables, permitiendo focalizar el desarrollo del presente módulo en la inteligencia y capacidad predictiva del sistema.

---

### 1. Análisis de Caso de Negocio, Benchmark y EDA (Actividad A1 — 30 hs)
*   **Descripción Detallada:** Documento interactivo y ejecutable (Jupyter Notebook) que consolida el análisis estadístico preliminar sobre los conjuntos de datos reales de métricas de infraestructura (CPU, memoria, red, latencias) provistos por el laboratorio GIDAS. Incluye además un relevamiento del estado del arte y un benchmark de mercado frente a herramientas como Grafana, Datadog y New Relic.
*   **Criterios de Aceptación (DoD):** 
    *   Definición clara del nicho del producto IntellOps basada en el benchmark.
    *   Análisis estadístico de distribuciones y correlaciones temporales del dataset inicial.
    *   Identificación matemática de valores atípicos (outliers) y formulación de hipótesis estadísticas para la detección de anomalías en métricas RUM.

### 2. Diseño Arquitectónico y Selección de Stack (Actividad A2 — 25 hs)
*   **Descripción Detallada:** Definición de la arquitectura del subsistema de Inteligencia Artificial dentro de la topología de contenedores de IntellOps (`intellops-ai-engine`).
*   **Criterios de Aceptación (DoD):**
    *   Documentación mediante ADRs (Architecture Decision Records) justificando la selección del stack tecnológico frente a restricciones de hardware (CPU-only, footprint < 50MB RAM para algoritmos clásicos).
    *   Definición del contrato de entrada/salida para el motor ML, asegurando el desacoplamiento con el backend principal y garantizando una integración estable.

### 3. Agente Predictivo y Backend de Procesamiento ML (Actividad A3 — 40 hs)
*   **Descripción Detallada:** Evolución estratégica del diseño inicial. Gracias a la consolidación temprana de la Ingesta RUM en el Núcleo Transversal del equipo (gestionada colaborativamente), el esfuerzo de esta etapa se orientó al desarrollo del **Agente Autónomo de Detección (AI Worker)**. En lugar de limitarse a una captura pasiva en el navegador, este agente se despliega en el backend aislado para capturar y consumir de forma asíncrona los lotes de métricas previamente normalizados en la base de datos.
*   **Criterios de Aceptación (DoD):**
    *   El worker asíncrono extrae y formatea correctamente los flujos de datos sin competir por recursos con la ingesta principal de la plataforma.
    *   El agente inyecta los datos preparados hacia los modelos predictivos y maneja los errores o indisponibilidades de la red/base de datos con estrategias de resiliencia.

### 4. Implementación de Modelos ML y Motor de Reglas (Actividad A4 — 50 hs)
*   **Descripción Detallada:** Repositorio central (scripts en Python) responsable de la ingeniería de características (*feature engineering*) y el motor de inferencia algorítmica.
*   **Criterios de Aceptación (DoD):**
    *   Implementación y evaluación comparativa entre algoritmos de detección de outliers (Isolation Forest) y modelos secuenciales o estadísticos (evaluación de LSTM/Prophet para proyección a futuro).
    *   La selección del modelo definitivo fundamentada en métricas de precisión, recall, F1-score y coste computacional.
    *   Implementación del **Motor de Reglas de Alerta**, un módulo lógico que evalúa el *score* de la IA y umbrales dinámicos, emitiendo el evento de anomalía (`expected_value`, `actual_value`, `severity_score`, `confidence_score`) hacia el gestor central de notificaciones del equipo.

### 5. Dashboard Interactivo IA - Frontend (Actividad A5 — 35 hs)
*   **Descripción Detallada:** Interfaz gráfica de usuario (*Single Page Application* en React/Angular) desarrollada como la herramienta visual de la capa predictiva del sistema.
*   **Criterios de Aceptación (DoD):**
    *   Integración exitosa con la API del backend.
    *   Despliegue operativo de al menos tres (3) vistas clave: 
        1. Panel de latencias y métricas RUM.
        2. Mapa de calor (*heatmap*) para analizar el comportamiento agrupado del usuario.
        3. Panel gerencial de predicciones, detallando anomalías detectadas y sus respectivos scores de confianza.

### 6. Testing, Validación e Informe Final de PPS (Actividades A6 y A7 — 20 hs)
*   **Descripción Detallada:** Consolidación de las métricas de calidad del prototipo y redacción del reporte académico técnico-científico exigido por la coordinación de PPS de la carrera.
*   **Criterios de Aceptación (DoD):**
    *   **(A6 - 10 hs):** Ejecución de pruebas de integración *end-to-end* (E2E) inyectando datos reales del laboratorio, midiendo formalmente la tasa de falsos positivos y la efectividad en la detección temprana.
    *   **(A7 - 10 hs):** Documentación exhaustiva que incluya limitaciones, ajustes del prototipo, reproducibilidad del entorno y anexo de código fuente. Redacción estructurada sirviendo como base para publicación científica (JAIIO / CACIC).

---
**Total Horas Certificadas:** 200 hs.