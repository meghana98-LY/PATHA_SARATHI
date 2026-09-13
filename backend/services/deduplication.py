import math
from datetime import datetime, timezone
from backend.database.connection import get_db_connection

def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculates great-circle distance between two points in meters.
    """
    R = 6371000  # Earth radius in meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2.0) ** 2 + \
        math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c

def process_hazard_deduplication(hazard_type, latitude, longitude, confidence, radius_meters=15.0):
    """
    Checks if a reported hazard already exists within radius_meters.
    If match found: increments report count and updates timestamp.
    If new: creates a new incident entry in the database.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    now_iso = datetime.now(timezone.utc).isoformat()

    cursor.execute("SELECT * FROM incidents WHERE hazard_type = ?", (hazard_type,))
    existing_incidents = cursor.fetchall()

    matched_incident = None
    for incident in existing_incidents:
        dist = haversine_distance(latitude, longitude, incident["latitude"], incident["longitude"])
        if dist <= radius_meters:
            matched_incident = incident
            break

    if matched_incident:
        # Update existing incident duplicate
        new_count = matched_incident["report_count"] + 1
        new_confidence = max(matched_incident["confidence"], confidence)
        
        cursor.execute("""
            UPDATE incidents 
            SET report_count = ?, confidence = ?, last_updated_at = ?
            WHERE id = ?
        """, (new_count, new_confidence, now_iso, matched_incident["id"]))
        
        conn.commit()
        conn.close()
        return {
            "action": "DEDUPLICATED",
            "incident_id": matched_incident["id"],
            "report_count": new_count
        }

    else:
        # Insert new incident
        incident_code = f"INC-{int(datetime.now().timestamp())}"
        cursor.execute("""
            INSERT INTO incidents (incident_code, hazard_type, latitude, longitude, confidence, first_reported_at, last_updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (incident_code, hazard_type, latitude, longitude, confidence, now_iso, now_iso))
        
        incident_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return {
            "action": "CREATED",
            "incident_id": incident_id,
            "incident_code": incident_code
        }