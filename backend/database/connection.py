import os
import psycopg2
from psycopg2.extras import RealDictCursor
from backend.config import Config

def get_db_connection():
    if not Config.DATABASE_URL:
        raise ValueError("DATABASE_URL is not set in environment or .env file!")
    
    conn = psycopg2.connect(Config.DATABASE_URL, cursor_factory=RealDictCursor)
    return conn

def init_db():
    """Initializes Neon PostgreSQL tables from schema.sql."""
    schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
    conn = get_db_connection()
    cursor = conn.cursor()
    
    with open(schema_path, "r", encoding="utf-8") as f:
        schema_script = f.read()
        
    cursor.execute(schema_script)
    conn.commit()
    cursor.close()
    conn.close()
    print("[INFO] NeonDB PostgreSQL schema synchronized successfully.")