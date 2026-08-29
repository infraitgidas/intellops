Diseño de Entidades ML (Alineación con DDL)
El ecosistema de Inteligencia Artificial de IntellOps persiste su estado utilizando tres entidades principales, cuyas estructuras mapean directamente a la base de datos relacional:

ML_MODEL: Gestiona el ciclo de vida y versionado de los algoritmos. 
model_id (UUID): Identificador único.
name (TEXT): Nombre descriptivo (ej. "IsolationForest-TTFB").
target_metric_id (SMALLINT): Métrica objetivo (ej. 1 para TTFB).
hyperparameters (JSONB): Parámetros de entrenamiento dinámicos. 
status_id (SMALLINT): Estado del modelo (1: training, 2: active, 3: deprecated).  

ANOMALY: Registra las desviaciones matemáticas detectadas por el algoritmo predictivo.  expected_value / actual_value (DOUBLE PRECISION): Núcleo de la desviación.  
severity_score / confidence_score (DOUBLE PRECISION): Puntuación de la criticidad y certeza de la inferencia matemática.
  
ALERT: Cola de mensajes en lenguaje natural listos para ser despachados.  
message (TEXT): Texto generado por el LLM.  
status_id (SMALLINT): Estado en la cola (1: Pending).  