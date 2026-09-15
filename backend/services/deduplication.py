import json
import math
from datetime import datetime, timezone
from backend.database.connection import get_db_connection
from backend.services.prioritization import calculate_priority_score
from backend.services.verification import evaluate_incident_verification
from backend.config import Config

def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371000.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2.0)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0)**2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c

def process_hazard_deduplication(device_id, timestamp, location, hazard, radius_meters=Config.DEDUPLICATION_RADIUS_METERS):
    lat = float(location.get("latitude", 0.0))
    lng = float(location.get("longitude", 0.0))
    speed_kmh = float(location.get("speed_kmh", 0.0))
    
    hazard_type = hazard.get("hazard_type", "Pothole")
    raw_class = hazard.get("raw_class", "")
    confidence = float(hazard.get("confidence", 0.70))
    bbox = json.dumps(hazard.get("bbox", []))
    image_data = hazard.get("image_data", None)  # Base64 string or URL

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM incidents WHERE status != 'RESOLVED'")
    incidents = cursor.fetchall()

    matched_incident = None
    for incident in incidents:
        dist = haversine_distance(lat, lng, incident["latitude"], incident["longitude"])
        if dist <= radius_meters and incident["hazard_type"] == hazard_type:
            matched_incident = incident
            break

    now_iso = datetime.now(timezone.utc)

    if matched_incident:
        incident_id = matched_incident["id"]
        new_count = matched_incident["report_count"] + 1
        new_confidence = max(matched_incident["confidence"], confidence)
        new_priority = calculate_priority_score(hazard_type, new_confidence, new_count, speed_kmh)

        # If existing incident doesn't have an image, update it with the new one
        updated_image = image_data if image_data else matched_incident["image_data"]

        cursor.execute("""
            UPDATE incidents 
            SET report_count = %s, confidence = %s, priority_score = %s, image_data = %s, last_updated_at = %s
            WHERE id = %s
        """, (new_count, new_confidence, new_priority, updated_image, now_iso, incident_id))
        
        action = "DEDUPLICATED"
    else:
        inc_code = f"INC-{int(datetime.now(timezone.utc).timestamp())}"
        initial_priority = calculate_priority_score(hazard_type, confidence, 1, speed_kmh)

        cursor.execute("""
            INSERT INTO incidents (incident_code, hazard_type, latitude, longitude, priority_score, confidence, report_count, image_data, first_reported_at, last_updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, 1, %s, %s, %s)
            RETURNING id
        """, (inc_code, hazard_type, lat, lng, initial_priority, confidence, image_data, now_iso, now_iso))

        incident_id = cursor.fetchone()["id"]
        action = "CREATED"

    # Store detection log with image
    cursor.execute("""
        INSERT INTO detection_logs (incident_id, device_id, raw_class, bbox, image_data, latitude, longitude, confidence, speed_kmh, timestamp)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (incident_id, device_id, raw_class, bbox, image_data, lat, lng, confidence, speed_kmh, timestamp or now_iso))

    conn.commit()
    cursor.close()
    conn.close()

    # Trigger automated verification
    evaluate_incident_verification(incident_id)

    return {"action": action, "incident_id": incident_id, "status": "SUCCESS"}