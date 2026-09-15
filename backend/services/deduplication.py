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

    # ---------------------------------------------------------
    # STEP 1: Find nearby ACTIVE / UNRESOLVED incident
    # ---------------------------------------------------------
    cursor.execute(
        "SELECT * FROM incidents WHERE status != 'RESOLVED'"
    )
    active_incidents = cursor.fetchall()

    matched_incident = None

    for incident in active_incidents:
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

    # ---------------------------------------------------------
    # STEP 2: If no active incident, search RESOLVED incidents
    #         to detect recurrence.
    # ---------------------------------------------------------
    previous_resolved_incident = None

    if matched_incident is None:
        cursor.execute(
            "SELECT * FROM incidents WHERE status = 'RESOLVED'"
        )
        resolved_incidents = cursor.fetchall()

        for incident in resolved_incidents:
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
                previous_resolved_incident = incident
                break

    now_iso = datetime.now(timezone.utc).isoformat()

    # ---------------------------------------------------------
    # STEP 3: Remember verification state for active incident
    # ---------------------------------------------------------
    was_verified = (
        matched_incident is not None
        and matched_incident["verification_status"] == "VERIFIED"
    )

    # ---------------------------------------------------------
    # CASE A: Existing ACTIVE incident -> DEDUPLICATE
    # ---------------------------------------------------------
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

    # ---------------------------------------------------------
    # CASE B: Previous RESOLVED incident -> REOCCURRENCE
    # ---------------------------------------------------------
    elif previous_resolved_incident:

        previous_incident_id = previous_resolved_incident["id"]

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
                verification_status,
                status,
                occurrence_type,
                previous_incident_id,
                first_reported_at,
                last_updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, 1, 'UNVERIFIED',
                    'REPORTED', 'REOCCURRENCE', ?, ?, ?)
            """,
            (
                inc_code,
                hazard_type,
                lat,
                lng,
                initial_priority,
                confidence,
                previous_incident_id,
                now_iso,
                now_iso,
            ),
        )

        incident_id = cursor.lastrowid

        action = "REOCCURRENCE"

    # ---------------------------------------------------------
    # CASE C: No nearby incident -> NEW
    # ---------------------------------------------------------
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
                verification_status,
                status,
                occurrence_type,
                previous_incident_id,
                first_reported_at,
                last_updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, 1, 'UNVERIFIED',
                    'REPORTED', 'NEW', NULL, ?, ?)
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

    # ---------------------------------------------------------
    # STEP 4: Store Edge AI detection log
    # ---------------------------------------------------------
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

    # ---------------------------------------------------------
    # STEP 5: Automatic verification
    # ---------------------------------------------------------
    verification_status = evaluate_incident_verification(
        incident_id
    )

    # ---------------------------------------------------------
    # STEP 6: Authority alert
    # ---------------------------------------------------------
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

    # ---------------------------------------------------------
    # STEP 7: Return result
    # ---------------------------------------------------------
    result = {
        "action": action,
        "incident_id": incident_id,
        "status": "SUCCESS",
        "verification_status": verification_status,
    }

    # Include recurrence information
    if action == "REOCCURRENCE":
        result["occurrence_type"] = "REOCCURRENCE"
        result["previous_incident_id"] = previous_resolved_incident["id"]
        result["previous_incident_code"] = (
            previous_resolved_incident["incident_code"]
        )

    elif action == "CREATED":
        result["occurrence_type"] = "NEW"

    if alert:
        result["authority_alert"] = alert

    return result