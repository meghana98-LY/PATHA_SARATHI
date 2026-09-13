import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "patha_sarathi.db")

def get_db_connection():
    """
    Establishes connection to the SQLite database.
    Creates tables automatically if they do not exist.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS incidents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            incident_code TEXT UNIQUE,
            hazard_type TEXT NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            confidence REAL NOT NULL,
            report_count INTEGER DEFAULT 1,
            status TEXT DEFAULT 'REPORTED',
            first_reported_at TEXT NOT NULL,
            last_updated_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

# Ensure table exists upon import
init_db()