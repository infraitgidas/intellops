 Pipeline Conceptual y Flujo Híbrido (ML + LLM)

El motor opera bajo un paradigma de análisis asimétrico, delegando el cálculo intensivo al modelo estadístico y la traducción cognitiva al modelo fundacional generativo. 

Tareas por Motor (Flujo Híbrido)

Fase 1: Motor Estadístico (Isolation Forest)

Objetivo: Detección de outliers matemáticos en series temporales.Acción: Ingesta el Feature Vector (agrupaciones temporales, promedios, desviaciones). Calcula el Z-Score. Si el actual_value excede el umbral de tolerancia frente al expected_value, determina que existe una anomalía y calcula el severity_score. Persiste el objeto en la tabla ANOMALY.  

Fase 2: Traductor Semántico (Llama 3.2 1B Local)

Objetivo: Comprensión cognitiva y generación de lenguaje natural.  Acción: Despertado por la creación de una anomalía, el LLM consume el JSON de la Fase 1. Inyecta el actual_value, expected_value y la métrica afectada en un Prompt Template interno. Genera el texto legible y crea un registro en ALERT con estado Pending (status_id: 1).  

flowchart TD
    A[(PostgreSQL: rum_metric)] -->|Consulta Batch| B(Feature Engineering)
    B -->|Feature Vector| C{Motor Matemático\nIsolation Forest}
    
    C -->|Normal| D[Fin del ciclo]
    C -->|Z-Score > Umbral| E[Generar ANOMALY]
    
    E -->|expected_value\nactual_value| F{Traductor Semántico\nLlama 3.2 1B}
    F -->|Texto Natural| G[Generar ALERT\nStatus: Pending]
    
    G --> H[(PostgreSQL: alert)]
    
    classDef math fill:#e1bee7,stroke:#8e24aa,stroke-width:2px;
    classDef llm fill:#bbdefb,stroke:#1e88e5,stroke-width:2px;
    class C math;
    class F llm;