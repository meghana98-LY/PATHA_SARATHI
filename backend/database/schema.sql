CREATE TABLE IF NOT EXISTS incidents (
    id SERIAL PRIMARY KEY,
    incident_code VARCHAR(64) UNIQUE NOT NULL,
    hazard_type VARCHAR(64) NOT NULL,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    priority_score DOUBLE PRECISION DEFAULT 50.0,
    confidence DOUBLE PRECISION DEFAULT 0.70,
    report_count INTEGER DEFAULT 1,
    verification_status VARCHAR(32) DEFAULT 'UNVERIFIED',
    status VARCHAR(32) DEFAULT 'REPORTED',
    image_data TEXT,
    first_reported_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    last_updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS detection_logs (
    id SERIAL PRIMARY KEY,
    incident_id INTEGER REFERENCES incidents(id) ON DELETE CASCADE,
    device_id VARCHAR(64) NOT NULL,
    raw_class VARCHAR(64),
    bbox TEXT,
    image_data TEXT,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    confidence DOUBLE PRECISION NOT NULL,
    speed_kmh DOUBLE PRECISION DEFAULT 0.0,
    timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS citizen_reports (
    id SERIAL PRIMARY KEY,
    incident_id INTEGER REFERENCES incidents(id) ON DELETE SET NULL,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    hazard_type VARCHAR(64) NOT NULL,
    image_data TEXT,
    notes TEXT,
    reported_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS authority_alerts (
    id SERIAL PRIMARY KEY,
    incident_id INTEGER REFERENCES incidents(id) ON DELETE CASCADE,
    alert_type VARCHAR(64) NOT NULL,
    priority_level VARCHAR(32) NOT NULL,
    message TEXT,
    dispatched_to VARCHAR(128),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);