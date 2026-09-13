-- Patha Sarathi Core Database Schema

CREATE TABLE IF NOT EXISTS incidents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    incident_code TEXT UNIQUE NOT NULL,
    hazard_type TEXT NOT NULL,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    priority_score REAL DEFAULT 0.0,
    confidence REAL NOT NULL,
    report_count INTEGER DEFAULT 1,
    verification_status TEXT DEFAULT 'UNVERIFIED', -- UNVERIFIED, VERIFIED, REJECTED
    status TEXT DEFAULT 'REPORTED',               -- REPORTED, IN_PROGRESS, RESOLVED
    first_reported_at TEXT NOT NULL,
    last_updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS detection_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    incident_id INTEGER,
    device_id TEXT NOT NULL,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    confidence REAL NOT NULL,
    speed_kmh REAL DEFAULT 0.0,
    timestamp TEXT NOT NULL,
    FOREIGN KEY(incident_id) REFERENCES incidents(id)
);

CREATE TABLE IF NOT EXISTS citizen_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    incident_id INTEGER,
    user_id TEXT DEFAULT 'ANONYMOUS',
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    notes TEXT,
    timestamp TEXT NOT NULL,
    FOREIGN KEY(incident_id) REFERENCES incidents(id)
);