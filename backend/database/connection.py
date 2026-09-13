import sqlite3
import os
from backend.config import Config

def get_db_connection():
    os.makedirs(os.path.dirname(Config.DB_PATH), exist_ok=True)
    conn = sqlite3.connect(Config.DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes SQLite database using schema.sql as single source of truth."""
    schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
    conn = get_db_connection()
    cursor = conn.cursor()
    
    with open(schema_path, "r") as f:
        schema_script = f.read()
        
    cursor.executescript(schema_script)
    conn.commit()
    conn.close()
    print("[INFO] Database schema synchronized from schema.sql.")