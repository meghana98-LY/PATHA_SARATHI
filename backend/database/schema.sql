-- NeonDB (PostgreSQL) Schema for PATHA_SARATHI

CREATE TABLE IF NOT EXISTS incidents (
    id SERIAL PRIMARY KEY,
    incident_code VARCHAR(100) UNIQUE NOT NULL,
    hazard_type VARCHAR(50) NOT NULL,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    priority_score DOUBLE PRECISION DEFAULT 0.0,
    confidence DOUBLE PRECISION NOT NULL,
    report_count INT DEFAULT 1,
    verification_status VARCHAR(20) DEFAULT 'UNVERIFIED', -- UNVERIFIED, VERIFIED, REJECTED
    status VARCHAR(20) DEFAULT 'REPORTED',               -- REPORTED, IN_PROGRESS, RESOLVED
    image_data TEXT,                                     -- Base64 string or Cloud Image URL
    first_reported_at TIMESTAMPTZ NOT NULL,
    last_updated_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS detection_logs (
    id SERIAL PRIMARY KEY,
    incident_id INT REFERENCES incidents(id) ON DELETE CASCADE,
    device_id VARCHAR(100) NOT NULL,
    raw_class VARCHAR(50),
    bbox TEXT,
    image_data TEXT,                                     -- Snapshot for this specific detection
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    confidence DOUBLE PRECISION NOT NULL,
    speed_kmh DOUBLE PRECISION DEFAULT 0.0,
    timestamp TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS citizen_reports (
    id SERIAL PRIMARY KEY,
    incident_id INT REFERENCES incidents(id) ON DELETE CASCADE,
    user_id VARCHAR(100) DEFAULT 'ANONYMOUS',
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    image_data TEXT,
    notes TEXT,
    timestamp TIMESTAMPTZ NOT NULL
);