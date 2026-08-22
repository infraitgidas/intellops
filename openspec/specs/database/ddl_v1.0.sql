-- DDL v1.0 — Generado desde DER v1.2 (ISS-S1-02)
-- Fecha: 2026-08-22
-- Entidades: APPLICATION, LAB_USER, USER_FAVORITE_METRIC, USER_SESSION, RUM_METRIC, JS_EXCEPTION, ML_MODEL, ANOMALY, ALERT
-- Base: SQLite (migrable a TimescaleDB)

-- ============================================================
-- Tabla: APPLICATION
-- ============================================================
-- Propósito: Gestiona el entorno multi-tenant. Contiene los api_token
-- que identifican de dónde provienen los datos.
-- ============================================================
CREATE TABLE IF NOT EXISTS application (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    api_token TEXT UNIQUE NOT NULL
);

-- Índice para búsquedas por api_token (usado en validación de auth)
CREATE INDEX IF NOT EXISTS idx_application_api_token ON application(api_token);

-- ============================================================
-- Tabla: LAB_USER
-- ============================================================
-- Propósito: Usuarios del laboratorio con acceso al sistema.
-- El Core gestiona el entorno multi-tenant a través de esta tabla.
-- ============================================================
CREATE TABLE IF NOT EXISTS lab_user (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    email TEXT UNIQUE,
    hashed_password TEXT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_superuser BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- Tabla: USER_FAVORITE_METRIC
-- ============================================================
-- Propósito: Métricas favoritas de cada usuario para quick access en dashboard.
-- ============================================================
CREATE TABLE IF NOT EXISTS user_favorite_metric (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    metric_name TEXT NOT NULL,
    metric_source TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, metric_name),
    FOREIGN KEY (user_id) REFERENCES lab_user(id) ON DELETE CASCADE
);

-- Índice para búsquedas por usuario
CREATE INDEX IF NOT EXISTS idx_ufm_user_id ON user_favorite_metric(user_id);

-- ============================================================
-- Tabla: USER_SESSION
-- ============================================================
-- Propósito: Sesiones de usuario activas para tracking de contexto.
-- ============================================================
CREATE TABLE IF NOT EXISTS user_session (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    token TEXT UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES lab_user(id) ON DELETE CASCADE
);

-- Índice para búsquedas por token (validación de sesión)
CREATE INDEX IF NOT EXISTS idx_user_session_token ON user_session(token);

-- ============================================================
-- Tabla: RUM_METRIC
-- ============================================================
-- Propósito: Métricas RUM (Real User Monitoring) recopiladas del agente JavaScript.
-- Almacenamiento optimizado para queries temporales y agregaciones.
-- ============================================================
CREATE TABLE IF NOT EXISTS rum_metric (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    metric_name TEXT NOT NULL,
    value REAL NOT NULL,
    unit TEXT,
    tags JSON DEFAULT '{}',
    timestamp INTEGER NOT NULL,
    source TEXT
);

CREATE INDEX IF NOT EXISTS idx_rum_name ON rum_metric(metric_name);
CREATE INDEX IF NOT EXISTS idx_rum_timestamp ON rum_metric(timestamp);

-- ============================================================
-- Tabla: JS_EXCEPTION
-- ============================================================
-- Propósito: Excepciones capturadas por el agente RUM del navegador.
-- Almacena el stack trace y metadata para análisis de errores frontend.
-- ============================================================
CREATE TABLE IF NOT EXISTS js_exception (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message TEXT NOT NULL,
    stack_trace TEXT,
    filename TEXT,
    lineno INTEGER,
    colno INTEGER,
    url TEXT,
    severity TEXT DEFAULT 'medium',
    timestamp INTEGER NOT NULL,
    -- Relación con métrica RUM opcional
    rum_metric_id INTEGER,
    FOREIGN KEY (rum_metric_id) REFERENCES rum_metric(id) ON DELETE SET NULL
);

-- Índice para búsquedas por severidad y tiempo
CREATE INDEX IF NOT EXISTS idx_js_exception_severity ON js_exception(severity, timestamp);

-- ============================================================
-- Tabla: ML_MODEL
-- ============================================================
-- Propósito: Almacena metadatos de los modelos ML entrenados y configuración.
-- El sistema usa Llama 3.2 1B GGUF 4-bit en recursos escasos.
-- ============================================================
CREATE TABLE IF NOT EXISTS ml_model (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    model_name TEXT NOT NULL UNIQUE,
    version TEXT NOT NULL,
    size_bytes INTEGER,
    format TEXT DEFAULT 'GGUF',
    n_gpu_layers INTEGER DEFAULT 0,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- ============================================================
-- Tabla: ANOMALY
-- ============================================================
-- Propósito: Anomalías detectadas por el motor ML/estadístico.
-- Flujo: detección → inserción de evento → generación de alerta.
-- ============================================================
CREATE TABLE IF NOT EXISTS anomaly (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rum_metric_id INTEGER NOT NULL,
    score REAL NOT NULL,
    severity TEXT NOT NULL,
    detector TEXT NOT NULL,
    description TEXT,
    expected_value REAL,
    actual_value REAL,
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'pending',
    FOREIGN KEY (rum_metric_id) REFERENCES rum_metric(id) ON DELETE CASCADE
);

-- Índices para queries de alertas y detección
CREATE INDEX IF NOT EXISTS idx_anomaly_severity ON anomaly(severity, detected_at);
CREATE INDEX IF NOT EXISTS idx_anomaly_status ON anomaly(status);

-- ============================================================
-- Tabla: ALERT
-- ============================================================
-- Propósito: Alertas generadas a partir de anomalías detectadas.
-- Flujo: ANOMALY → reglas de negocio → ALERT (estado pending → sent/failed)
-- ============================================================
CREATE TABLE IF NOT EXISTS alert (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    anomaly_id INTEGER NOT NULL,
    message TEXT NOT NULL,
    severity TEXT NOT NULL,
    status TEXT DEFAULT 'pending',
    sent_at TIMESTAMP,
    channel TEXT,  -- 'telegram', 'slack', 'email', 'discord'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (anomaly_id) REFERENCES anomaly(id) ON DELETE CASCADE
);

-- Índices para gestión de alertas
CREATE INDEX IF NOT EXISTS idx_alert_status ON alert(status, created_at);
CREATE INDEX IF NOT EXISTS idx_alert_channel ON alert(channel);

-- ============================================================
-- Vista: resumen_observabilidad
-- ============================================================
-- Proporciona una vista consolidada para el dashboard y el asistente GenIA.
-- ============================================================
CREATE VIEW IF NOT EXISTS v_observability_summary AS
SELECT
    'application' AS entity_type,
    COUNT(*) AS total_records,
    MAX(created_at) AS last_activity
FROM application
UNION ALL
SELECT
    'lab_user' AS entity_type,
    COUNT(*) AS total_records,
    MAX(created_at) AS last_activity
FROM lab_user
UNION ALL
SELECT
    'rum_metric' AS entity_type,
    COUNT(*) AS total_records,
    MAX(timestamp) AS last_data_point
FROM rum_metric
UNION ALL
SELECT
    'anomaly' AS entity_type,
    COUNT(*) AS total_records,
    MAX(detected_at) AS last_detection
FROM anomaly
UNION ALL
SELECT
    'alert' AS entity_type,
    COUNT(*) AS total_records,
    MAX(created_at) AS last_alert
FROM alert;