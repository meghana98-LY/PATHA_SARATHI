import json
import math
from datetime import datetime, timezone

from backend.database.connection import get_db_connection
from backend.services.prioritization import calculate_priority_score
from backend.services.verification import evaluate_incident_verification
from backend.config import Config
from authority.alert_service import process_incident


def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371000.0

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1)
        * math.cos(phi2)
        * math.sin(delta_lambda / 2.0) ** 2
    )

    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))

    return R * c


def process_hazard_deduplication(
    device_id,
    timestamp,
    location,
    hazard,
    radius_meters=Config.DEDUPLICATION_RADIUS_METERS,
):
    lat = float(location.get("latitude", 0.0))
    lng = float(location.get("longitude", 0.0))
    speed_kmh = float(location.get("speed_kmh", 0.0))

    hazard_type = hazard.get("hazard_type", "Pothole")
    raw_class = hazard.get("raw_class", "")
    confidence = float(hazard.get("confidence", 0.70))
    bbox = json.dumps(hazard.get("bbox", []))

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM incidents WHERE status != 'RESOLVED'"
    )
    incidents = cursor.fetchall()

    matched_incident = None

    for incident in incidents:
        dist = haversine_distance(
            lat,
            lng,
            incident["latitude"],
            incident["longitude"],
        )

        if (
            dist <= radius_meters
            and incident["hazard_type"] == hazard_type
        ):
            matched_incident = incident
            break

    now_iso = datetime.now(timezone.utc).isoformat()

    # Remember whether the matched incident was already verified.
    # This prevents duplicate authority alerts.
    was_verified = (
        matched_incident is not None
        and matched_incident["verification_status"] == "VERIFIED"
    )

    if matched_incident:
        incident_id = matched_incident["id"]

        new_count = matched_incident["report_count"] + 1
        new_confidence = max(
            matched_incident["confidence"],
            confidence,
        )

        new_priority = calculate_priority_score(
            hazard_type,
            new_confidence,
            new_count,
            speed_kmh,
        )

        cursor.execute(
            """
            UPDATE incidents
            SET report_count = ?,
                confidence = ?,
                priority_score = ?,
                last_updated_at = ?
            WHERE id = ?
            """,
            (
                new_count,
                new_confidence,
                new_priority,
                now_iso,
                incident_id,
            ),
        )

        action = "DEDUPLICATED"

    else:
        inc_code = (
            f"INC-{int(datetime.now(timezone.utc).timestamp())}"
        )

        initial_priority = calculate_priority_score(
            hazard_type,
            confidence,
            1,
            speed_kmh,
        )

        cursor.execute(
            """
            INSERT INTO incidents (
                incident_code,
                hazard_type,
                latitude,
                longitude,
                priority_score,
                confidence,
                report_count,
                first_reported_at,
                last_updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?)
            """,
            (
                inc_code,
                hazard_type,
                lat,
                lng,
                initial_priority,
                confidence,
                now_iso,
                now_iso,
            ),
        )

        incident_id = cursor.lastrowid
        action = "CREATED"

    # Store the complete Edge AI detection log.
    cursor.execute(
        """
        INSERT INTO detection_logs (
            incident_id,
            device_id,
            raw_class,
            bbox,
            latitude,
            longitude,
            confidence,
            speed_kmh,
            timestamp
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            incident_id,
            device_id,
            raw_class,
            bbox,
            lat,
            lng,
            confidence,
            speed_kmh,
            timestamp,
        ),
    )

    conn.commit()
    conn.close()

    # Trigger automatic verification.
    verification_status = evaluate_incident_verification(
        incident_id
    )

    # Create an authority alert only when the incident becomes
    # newly verified. This prevents repeated alerts for duplicates.
    alert = None

    if verification_status == "VERIFIED" and not was_verified:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM incidents WHERE id = ?",
            (incident_id,),
        )

        incident = cursor.fetchone()
        conn.close()

        if incident:
            alert = process_incident(dict(incident))

    result = {
        "action": action,
        "incident_id": incident_id,
        "status": "SUCCESS",
        "verification_status": verification_status,
    }

    if alert:
        result["authority_alert"] = alert

    return result