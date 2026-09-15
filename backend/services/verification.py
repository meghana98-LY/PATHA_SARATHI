from backend.database.connection import get_db_connection

def evaluate_incident_verification(incident_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM incidents WHERE id = %s", (incident_id,))
    incident = cursor.fetchone()

    if not incident:
        cursor.close()
        conn.close()
        return "NOT_FOUND"

    confidence = incident["confidence"]
    report_count = incident["report_count"]

    if confidence >= 0.85 or report_count >= 3:
        new_status = "VERIFIED"
    else:
        new_status = "UNVERIFIED"

    cursor.execute(
        "UPDATE incidents SET verification_status = %s WHERE id = %s",
        (new_status, incident_id)
    )
    conn.commit()
    cursor.close()
    conn.close()

    return new_status