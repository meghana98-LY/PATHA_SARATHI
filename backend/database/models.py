import os
from backend.database.connection import get_db_connection

def initialize_database_from_sql():
    """
    Executes schema.sql to ensure all database tables and indexes exist.
    """
    schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
    if not os.path.exists(schema_path):
        return

    conn = get_db_connection()
    with open(schema_path, "r") as f:
        schema_script = f.read()

    cursor = conn.cursor()
    cursor.executescript(schema_script)
    conn.commit()
    conn.close()

class IncidentModel:
    @staticmethod
    def get_all():
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM incidents ORDER BY priority_score DESC, last_updated_at DESC")
        rows = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return rows

    @staticmethod
    def get_by_id(incident_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM incidents WHERE id = ?", (incident_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    @staticmethod
    def update_status(incident_id, new_status):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE incidents SET status = ? WHERE id = ?", (new_status, incident_id))
        conn.commit()
        conn.close()