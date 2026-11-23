-- IntellOps - DDL PostgreSQL 16
-- DER v1.2 + catálogos de futura ampliación
-- PostgreSQL 16 + JSONB
--
-- Entidades principales: UUID
-- Tablas catálogo: SMALLINT GENERATED ALWAYS AS IDENTITY
-- Los valores booleanos se mantienen como BOOLEAN.

BEGIN;

-- ============================================================
-- 1. CATÁLOGOS
-- ============================================================

CREATE TABLE metric_type (
    metric_type_id SMALLINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    description TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE user_role (
    role_id SMALLINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name VARCHAR(30) NOT NULL UNIQUE,
    description TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE model_status (
    status_id SMALLINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name VARCHAR(30) NOT NULL UNIQUE,
    description TEXT
);

CREATE TABLE alert_status (
    status_id SMALLINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name VARCHAR(30) NOT NULL UNIQUE,
    description TEXT
);

CREATE TABLE alert_channel (
    channel_id SMALLINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name VARCHAR(30) NOT NULL UNIQUE,
    description TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);

-- ============================================================
-- 2. APPLICATION
-- ============================================================

CREATE TABLE application (
    app_id UUID PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    -- api_token_hash agregado por la migración 0002 (ISS-S2-01):
    -- columna dormida (ADR-03); uso en S2-02.
    api_token_hash VARCHAR(64),
    -- is_active agregado por la migración 0003 (ISS-S2-02, ADR-20):
    -- NOT NULL DEFAULT TRUE; apaga la key de ingesta en S2-02.
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Migración 0002: índice único parcial (solo hashes no NULL).
CREATE UNIQUE INDEX idx_application_api_token_hash
    ON application(api_token_hash)
    WHERE api_token_hash IS NOT NULL;

-- ============================================================
-- 3. LAB_USER
-- ============================================================

CREATE TABLE lab_user (
    user_id UUID PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    -- password_hash agregado por la migración 0002 (ISS-S2-01):
    -- nullable en DDL (ADR-06); el enforcement vive en el servicio.
    password_hash VARCHAR(255),
    role_id SMALLINT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    last_login TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_lab_user_role
        FOREIGN KEY (role_id)
        REFERENCES user_role(role_id)
        ON DELETE RESTRICT
);

CREATE INDEX idx_lab_user_role_id
    ON lab_user(role_id);

-- Migración 0002: email único (ISS-S2-01).
CREATE UNIQUE INDEX idx_lab_user_email
    ON lab_user(email);

-- ============================================================
-- 4. USER_FAVORITE_METRIC
-- ============================================================

CREATE TABLE user_favorite_metric (
    favorite_id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    metric_type_id SMALLINT NOT NULL,
    default_time_window TEXT NOT NULL,
    added_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_user_favorite_metric_user
        FOREIGN KEY (user_id)
        REFERENCES lab_user(user_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_user_favorite_metric_type
        FOREIGN KEY (metric_type_id)
        REFERENCES metric_type(metric_type_id)
        ON DELETE RESTRICT
);

CREATE INDEX idx_user_favorite_metric_user_id
    ON user_favorite_metric(user_id);

CREATE INDEX idx_user_favorite_metric_type_id
    ON user_favorite_metric(metric_type_id);

-- ============================================================
-- 5. USER_SESSION
-- ============================================================

CREATE TABLE user_session (
    session_id UUID PRIMARY KEY,
    app_id UUID NOT NULL,
    user_id UUID,
    ip_address TEXT,
    user_agent TEXT,
    os_version TEXT,
    start_timestamp TIMESTAMPTZ NOT NULL,
    end_timestamp TIMESTAMPTZ,
    duration_ms INTEGER,

    CONSTRAINT fk_user_session_application
        FOREIGN KEY (app_id)
        REFERENCES application(app_id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_user_session_user
        FOREIGN KEY (user_id)
        REFERENCES lab_user(user_id)
        ON DELETE SET NULL
);

CREATE INDEX idx_user_session_app_id
    ON user_session(app_id);

CREATE INDEX idx_user_session_user_id
    ON user_session(user_id);

-- ============================================================
-- 6. RUM_METRIC
-- ============================================================

CREATE TABLE rum_metric (
    metric_id UUID PRIMARY KEY,
    session_id UUID NOT NULL,
    metric_type_id SMALLINT NOT NULL,
    value DOUBLE PRECISION NOT NULL,
    unit TEXT NOT NULL,
    page_url TEXT,
    metadata JSONB,
    timestamp TIMESTAMPTZ NOT NULL,

    CONSTRAINT fk_rum_metric_session
        FOREIGN KEY (session_id)
        REFERENCES user_session(session_id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_rum_metric_type
        FOREIGN KEY (metric_type_id)
        REFERENCES metric_type(metric_type_id)
        ON DELETE RESTRICT
);

-- Índices definidos en el DER v1.2:
-- (session_id, timestamp)
-- (metric_type, timestamp DESC)
CREATE INDEX idx_rum_metric_session_timestamp
    ON rum_metric(session_id, timestamp);

CREATE INDEX idx_rum_metric_type_timestamp
    ON rum_metric(metric_type_id, timestamp DESC);

-- Búsqueda eficiente sobre metadata JSONB.
CREATE INDEX idx_rum_metric_metadata
    ON rum_metric USING GIN(metadata);

-- ============================================================
-- 7. JS_EXCEPTION
-- ============================================================

CREATE TABLE js_exception (
    error_id UUID PRIMARY KEY,
    session_id UUID NOT NULL,
    metric_id UUID,
    error_type TEXT NOT NULL,
    message TEXT NOT NULL,
    stack_trace TEXT,
    sample_rate DOUBLE PRECISION,
    timestamp TIMESTAMPTZ NOT NULL,

    CONSTRAINT fk_js_exception_session
        FOREIGN KEY (session_id)
        REFERENCES user_session(session_id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_js_exception_metric
        FOREIGN KEY (metric_id)
        REFERENCES rum_metric(metric_id)
        ON DELETE SET NULL
);

CREATE INDEX idx_js_exception_session_timestamp
    ON js_exception(session_id, timestamp);

-- ============================================================
-- 8. ML_MODEL
-- ============================================================

CREATE TABLE ml_model (
    model_id UUID PRIMARY KEY,
    name TEXT NOT NULL,
    target_metric_id SMALLINT NOT NULL,
    version TEXT NOT NULL,
    status_id SMALLINT NOT NULL,
    hyperparameters JSONB,
    last_trained_at TIMESTAMPTZ,

    CONSTRAINT fk_ml_model_target_metric
        FOREIGN KEY (target_metric_id)
        REFERENCES metric_type(metric_type_id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_ml_model_status
        FOREIGN KEY (status_id)
        REFERENCES model_status(status_id)
        ON DELETE RESTRICT
);

CREATE INDEX idx_ml_model_target_metric
    ON ml_model(target_metric_id);

CREATE INDEX idx_ml_model_status
    ON ml_model(status_id);

-- ============================================================
-- 9. ANOMALY
-- ============================================================

CREATE TABLE anomaly (
    anomaly_id UUID PRIMARY KEY,
    -- Ancla a la serie/bucket agregada (migración 0004, ISS-S3-04):
    -- reemplaza metric_id. timestamp = instante de detección.
    application_id UUID NOT NULL,
    metric_type_id SMALLINT NOT NULL,
    bucket_start TIMESTAMPTZ NOT NULL,
    bucket_seconds INTEGER NOT NULL,
    model_id UUID NOT NULL,
    expected_value DOUBLE PRECISION NOT NULL,
    actual_value DOUBLE PRECISION NOT NULL,
    severity_score DOUBLE PRECISION NOT NULL,
    confidence_score DOUBLE PRECISION NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,

    CONSTRAINT ck_anomaly_bucket_seconds
        CHECK (bucket_seconds >= 60),

    CONSTRAINT ck_anomaly_bucket_aligned
        CHECK ((EXTRACT(EPOCH FROM bucket_start)::bigint % bucket_seconds) = 0),

    CONSTRAINT fk_anomaly_application
        FOREIGN KEY (application_id)
        REFERENCES application(app_id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_anomaly_metric_type
        FOREIGN KEY (metric_type_id)
        REFERENCES metric_type(metric_type_id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_anomaly_model
        FOREIGN KEY (model_id)
        REFERENCES ml_model(model_id)
        ON DELETE RESTRICT
);

CREATE UNIQUE INDEX idx_anomaly_series_bucket_model
    ON anomaly(application_id, metric_type_id, bucket_start, bucket_seconds, model_id);

CREATE INDEX idx_anomaly_timestamp
    ON anomaly(timestamp);

CREATE INDEX idx_anomaly_model_id
    ON anomaly(model_id);

-- Read path de GET /anomalies, newest-first (migración 0007, ISS-B-03).
CREATE INDEX idx_anomaly_app_timestamp
    ON anomaly(application_id, timestamp DESC);

-- ============================================================
-- 10. ALERT
-- ============================================================

CREATE TABLE alert (
    alert_id UUID PRIMARY KEY,
    -- Alerta independiente de la anomalía (migración 0007, ISS-B-03, ADR-0012):
    -- application_id es el tenant; anomaly_id es NULL en las alertas de reglas
    -- de umbral (v1) y recipient/channel_id los completa el dispatcher (B.10)
    -- al despachar.
    application_id UUID NOT NULL,
    anomaly_id UUID,
    severity TEXT NOT NULL,
    recipient TEXT,
    channel_id SMALLINT,
    message TEXT NOT NULL,
    status_id SMALLINT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    sent_at TIMESTAMPTZ,
    -- Regla que creó la alerta, con su umbral y el valor observado (migración
    -- 0008, ISS-B-14). NULL en las alertas previas y en las de ML (M3).
    -- rule_id no es FK: los defaults viven en código y el cooldown se consulta
    -- por (application_id, rule_id).
    rule_id TEXT,
    threshold DOUBLE PRECISION,
    observed_value DOUBLE PRECISION,

    CONSTRAINT ck_alert_severity
        CHECK (severity IN ('low', 'medium', 'high', 'critical')),

    CONSTRAINT ck_alert_rule_id
        CHECK (rule_id IN ('latency', 'error_rate', 'availability')),

    CONSTRAINT fk_alert_application
        FOREIGN KEY (application_id)
        REFERENCES application(app_id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_alert_anomaly
        FOREIGN KEY (anomaly_id)
        REFERENCES anomaly(anomaly_id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_alert_channel
        FOREIGN KEY (channel_id)
        REFERENCES alert_channel(channel_id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_alert_status
        FOREIGN KEY (status_id)
        REFERENCES alert_status(status_id)
        ON DELETE RESTRICT
);

CREATE INDEX idx_alert_status
    ON alert(status_id);

CREATE INDEX idx_alert_channel
    ON alert(channel_id);

-- Read path de GET /alerts, newest-first (migración 0007, ISS-B-03).
CREATE INDEX idx_alert_app_created
    ON alert(application_id, created_at DESC);

-- ============================================================
-- 11. ALERT_RULE
-- ============================================================
-- Reglas de umbral por aplicación (migración 0008, ISS-B-14). Una fila
-- reemplaza por completo al default del código para su (application_id,
-- rule_id); sin fila rige el default. enabled = FALSE saltea la regla.

CREATE TABLE alert_rule (
    application_id UUID NOT NULL,
    rule_id TEXT NOT NULL,
    threshold DOUBLE PRECISION NOT NULL,
    severity TEXT NOT NULL,
    window_seconds INTEGER NOT NULL,
    min_samples INTEGER NOT NULL,
    cooldown_seconds INTEGER NOT NULL,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,

    CONSTRAINT pk_alert_rule
        PRIMARY KEY (application_id, rule_id),

    CONSTRAINT ck_alert_rule_rule_id
        CHECK (rule_id IN ('latency', 'error_rate', 'availability')),

    CONSTRAINT ck_alert_rule_severity
        CHECK (severity IN ('low', 'medium', 'high', 'critical')),

    CONSTRAINT ck_alert_rule_window
        CHECK (window_seconds >= 60),

    CONSTRAINT ck_alert_rule_min_samples
        CHECK (min_samples >= 1),

    CONSTRAINT ck_alert_rule_cooldown
        CHECK (cooldown_seconds >= 0),

    CONSTRAINT fk_alert_rule_application
        FOREIGN KEY (application_id)
        REFERENCES application(app_id)
        ON DELETE CASCADE
);

-- ============================================================
-- 12. DATOS INICIALES DE CATÁLOGOS
-- ============================================================

INSERT INTO metric_type (name, description)
VALUES
    ('TTFB', 'Time to First Byte'),
    ('FCP', 'First Contentful Paint'),
    ('XHR_LATENCY', 'Latencia de peticiones XHR/Fetch'),
    ('JS_EXCEPTION_RATE', 'Tasa de excepciones JavaScript'),
    ('RAGE_CLICK', 'Frecuencia de clics de frustración'),
    -- Fila agregada por la migración 0006 (ISS-B-13, B.13/D1): disponibilidad
    -- medida por la sonda HTTP, unidad `count`, valor 1 disponible / 0 no.
    ('AVAILABILITY', 'Disponibilidad medida por la sonda HTTP (1 disponible, 0 no disponible)');

INSERT INTO user_role (name, description)
VALUES
    ('Admin', 'Usuario administrador del sistema'),
    ('Researcher', 'Usuario investigador');

-- ============================================================
-- 13. SEED ADMIN (migración 0002, solo dev/CI)
-- ============================================================
-- Usuario de bootstrap con UUID fijo; password_hash argon2id de la
-- password dev (ADMIN_BOOTSTRAP_PASSWORD en .env.example). No usar en
-- producción: reemplazar por override de entorno/creación manual.

INSERT INTO lab_user (user_id, name, email, role_id, is_active, password_hash)
VALUES (
    '9f8c5a2e-1b2c-4d5e-8f9a-0b1c2d3e4f5a',
    'Admin',
    'admin@intellops.local',
    (SELECT role_id FROM user_role WHERE name = 'Admin'),
    TRUE,
    '$argon2id$v=19$m=65536,t=3,p=4$hH0jN7g+iu10ULAQCmU2lA$IucJ1e2Xsts65qYcSKoL9Zk1Z2zmQO2yDwQbxfQ2+qw'
);

INSERT INTO model_status (name, description)
VALUES
    ('training', 'Modelo actualmente en entrenamiento'),
    ('active', 'Modelo actualmente activo'),
    ('deprecated', 'Modelo reemplazado o fuera de uso');

INSERT INTO alert_status (name, description)
VALUES
    ('Pending', 'Alerta pendiente de envío'),
    ('Sent', 'Alerta enviada correctamente'),
    ('Failed', 'El envío de la alerta falló');

INSERT INTO alert_channel (name, description)
VALUES
    ('Telegram', 'Notificación mediante Telegram'),
    ('Email', 'Notificación mediante correo electrónico');

COMMIT;
