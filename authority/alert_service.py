from datetime import datetime, timezone
from uuid import uuid4

from authority.dispatch import create_dispatch
from authority.notification import send_notification
from backend.database.connection import get_db_connection


def calculate_priority(incident: dict) -> str:
    hazard_type = (
        incident.get("hazard_type")
        or incident.get("type")
        or ""
    ).lower().strip()

    confidence = float(incident.get("confidence", 0))
    report_count = int(incident.get("report_count", 1))

    critical_types = {
        "road obstruction",
        "damaged divider",
        "waterlogging",
    }

    if hazard_type in critical_types and confidence >= 0.75:
        return "critical"

    if confidence >= 0.85 and report_count >= 3:
        return "high"

    if confidence >= 0.85:
        return "high"

    if confidence >= 0.60:
        return "medium"

    return "low"


def _row_to_alert(row):
    if not row:
        return None

    return {
        "alert_id": row["alert_id"],
        "incident_id": row["incident_id"],
        "hazard_type": row["hazard_type"],
        "location": row["location"],
        "latitude": row["latitude"],
        "longitude": row["longitude"],
        "confidence": row["confidence"],
        "report_count": row["report_count"],
        "priority": row["priority"],
        "department": row["department"],
        "assigned_team": row["assigned_team"],
        "status": row["status"],
        "source": row["source"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def create_alert(incident: dict) -> dict:
    incident_id = (
        incident.get("incident_code")
        or incident.get("incident_id")
        or str(incident.get("id", "UNKNOWN"))
    )

    hazard_type = (
        incident.get("hazard_type")
        or incident.get("type")
        or "unknown"
    )

    priority = (
        incident.get("priority")
        or calculate_priority(incident)
    )

    # Prevent duplicate authority alerts for the same incident.
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT *
        FROM authority_alerts
        WHERE incident_id = ?
        ORDER BY id DESC
        LIMIT 1
        """,
        (str(incident_id),)
    )

    existing = cursor.fetchone()

    if existing:
        conn.close()
        return _row_to_alert(existing)

    alert_id = f"ALT-{uuid4().hex[:8].upper()}"
    created_at = datetime.now(timezone.utc).isoformat()

    alert = {
        "alert_id": alert_id,
        "incident_id": str(incident_id),
        "hazard_type": hazard_type,
        "location": incident.get("location", "Unknown"),
        "latitude": incident.get("latitude"),
        "longitude": incident.get("longitude"),
        "confidence": incident.get("confidence", 0),
        "report_count": incident.get("report_count", 1),
        "priority": priority,
        "department": None,
        "assigned_team": None,
        "status": "PENDING_ACTION",
        "source": incident.get("source", "backend"),
        "created_at": created_at,
        "updated_at": None,
    }

    dispatch = create_dispatch(alert)

    alert["department"] = dispatch["department"]
    alert["assigned_team"] = dispatch["assigned_team"]

    cursor.execute(
        """
        INSERT INTO authority_alerts (
            alert_id,
            incident_id,
            hazard_type,
            location,
            latitude,
            longitude,
            confidence,
            report_count,
            priority,
            department,
            assigned_team,
            status,
            source,
            created_at,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            alert["alert_id"],
            alert["incident_id"],
            alert["hazard_type"],
            alert["location"],
            alert["latitude"],
            alert["longitude"],
            alert["confidence"],
            alert["report_count"],
            alert["priority"],
            alert["department"],
            alert["assigned_team"],
            alert["status"],
            alert["source"],
            alert["created_at"],
            alert["updated_at"],
        ),
    )

    conn.commit()
    conn.close()

    return alert


def process_incident(incident: dict) -> dict:
    alert = create_alert(incident)
    notification = send_notification(alert)

    return {
        "alert": alert,
        "notification": notification,
    }


def get_all_alerts() -> list:
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT *
        FROM authority_alerts
        ORDER BY
            CASE priority
                WHEN 'critical' THEN 1
                WHEN 'high' THEN 2
                WHEN 'medium' THEN 3
                WHEN 'low' THEN 4
                ELSE 5
            END,
            created_at DESC
        """
    )

    rows = cursor.fetchall()
    conn.close()

    return [_row_to_alert(row) for row in rows]


def get_alert_by_id(alert_id: str):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT *
        FROM authority_alerts
        WHERE alert_id = ?
        """,
        (alert_id,)
    )

    row = cursor.fetchone()
    conn.close()

    return _row_to_alert(row)


def update_alert_status(alert_id: str, status: str):
    valid_statuses = {
        "PENDING_ACTION",
        "IN_PROGRESS",
        "RESOLVED",
        "REJECTED",
    }

    status = status.upper().strip()

    if status not in valid_statuses:
        raise ValueError(
            f"Invalid status. Allowed values: {valid_statuses}"
        )

    alert = get_alert_by_id(alert_id)

    if alert is None:
        return None

    updated_at = datetime.now(timezone.utc).isoformat()

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE authority_alerts
        SET status = ?,
            updated_at = ?
        WHERE alert_id = ?
        """,
        (
            status,
            updated_at,
            alert_id,
        ),
    )

    conn.commit()
    conn.close()

    return get_alert_by_id(alert_id)