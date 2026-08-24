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
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- 3. LAB_USER
-- ============================================================

CREATE TABLE lab_user (
    user_id UUID PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
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
    metric_id UUID NOT NULL,
    model_id UUID NOT NULL,
    expected_value DOUBLE PRECISION NOT NULL,
    actual_value DOUBLE PRECISION NOT NULL,
    severity_score DOUBLE PRECISION NOT NULL,
    confidence_score DOUBLE PRECISION NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,

    CONSTRAINT fk_anomaly_metric
        FOREIGN KEY (metric_id)
        REFERENCES rum_metric(metric_id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_anomaly_model
        FOREIGN KEY (model_id)
        REFERENCES ml_model(model_id)
        ON DELETE RESTRICT
);

CREATE INDEX idx_anomaly_timestamp
    ON anomaly(timestamp);

CREATE INDEX idx_anomaly_model_id
    ON anomaly(model_id);

-- ============================================================
-- 10. ALERT
-- ============================================================

CREATE TABLE alert (
    alert_id UUID PRIMARY KEY,
    anomaly_id UUID NOT NULL,
    recipient TEXT NOT NULL,
    channel_id SMALLINT NOT NULL,
    message TEXT NOT NULL,
    status_id SMALLINT NOT NULL,
    sent_at TIMESTAMPTZ,

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

-- ============================================================
-- 11. DATOS INICIALES DE CATÁLOGOS
-- ============================================================

INSERT INTO metric_type (name, description)
VALUES
    ('TTFB', 'Time to First Byte'),
    ('FCP', 'First Contentful Paint'),
    ('XHR_LATENCY', 'Latencia de peticiones XHR/Fetch'),
    ('JS_EXCEPTION_RATE', 'Tasa de excepciones JavaScript'),
    ('RAGE_CLICK', 'Frecuencia de clics de frustración');

INSERT INTO user_role (name, description)
VALUES
    ('Admin', 'Usuario administrador del sistema'),
    ('Researcher', 'Usuario investigador');

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
