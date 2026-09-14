CREATE TABLE IF NOT EXISTS incidents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    incident_code TEXT UNIQUE NOT NULL,
    hazard_type TEXT NOT NULL,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    priority_score REAL DEFAULT 0.0,
    confidence REAL NOT NULL,
    report_count INTEGER DEFAULT 1,
    verification_status TEXT DEFAULT 'UNVERIFIED',
    status TEXT DEFAULT 'REPORTED',
    first_reported_at TEXT NOT NULL,
    last_updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS detection_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    incident_id INTEGER,
    device_id TEXT NOT NULL,
    raw_class TEXT,
    bbox TEXT,
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

CREATE TABLE IF NOT EXISTS incidents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    incident_code TEXT UNIQUE NOT NULL,
    hazard_type TEXT NOT NULL,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    priority_score REAL DEFAULT 0.0,
    confidence REAL NOT NULL,
    report_count INTEGER DEFAULT 1,
    verification_status TEXT DEFAULT 'UNVERIFIED',
    status TEXT DEFAULT 'REPORTED',
    first_reported_at TEXT NOT NULL,
    last_updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS detection_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    incident_id INTEGER,
    device_id TEXT NOT NULL,
    raw_class TEXT,
    bbox TEXT,
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

CREATE TABLE IF NOT EXISTS authority_alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    alert_id TEXT UNIQUE NOT NULL,
    incident_id TEXT NOT NULL,
    hazard_type TEXT NOT NULL,
    location TEXT,
    latitude REAL,
    longitude REAL,
    confidence REAL DEFAULT 0.0,
    report_count INTEGER DEFAULT 1,
    priority TEXT NOT NULL,
    department TEXT,
    assigned_team TEXT,
    status TEXT DEFAULT 'PENDING_ACTION',
    source TEXT DEFAULT 'backend',
    created_at TEXT NOT NULL,
    updated_at TEXT
);