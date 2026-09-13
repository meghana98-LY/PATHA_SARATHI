from backend.database.connection import get_db_connection

def evaluate_incident_verification(incident_id):
    """
    Auto-verifies an incident if:
    1. AI confidence >= 0.85 OR
    2. Multiple independent reports exist (report_count >= 3)
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM incidents WHERE id = ?", (incident_id,))
    incident = cursor.fetchone()

    if not incident:
        conn.close()
        return "NOT_FOUND"

    confidence = incident["confidence"]
    report_count = incident["report_count"]

    if confidence >= 0.85 or report_count >= 3:
        new_status = "VERIFIED"
    else:
        new_status = "UNVERIFIED"

    cursor.execute(
        "UPDATE incidents SET verification_status = ? WHERE id = ?",
        (new_status, incident_id)
    )
    conn.commit()
    conn.close()

    return new_status