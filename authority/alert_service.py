# authority/alert_service.py

"""
PATHA SARATHI - Authority Alert Service

Responsibilities:
1. Calculate incident priority.
2. Create authority alerts.
3. Assign departments.
4. Generate notifications.
5. Track alert status.

This version supports the actual PATHA SARATHI
incident JSON format.
"""

from datetime import datetime, timezone
from uuid import uuid4

from authority.dispatch import create_dispatch
from authority.notification import send_notification


# Temporary in-memory alert storage.
# This is suitable for the prototype.
# Later, it can be replaced with the project database.
ALERTS = []


def calculate_priority(incident: dict) -> str:
    """
    Calculate priority using confidence, report count,
    and hazard type.

    Priority rules for the prototype:
    - CRITICAL: Dangerous hazard + high confidence
    - HIGH: High confidence and/or multiple reports
    - MEDIUM: Moderate confidence
    - LOW: Low confidence
    """

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


def create_alert(incident: dict) -> dict:
    """
    Convert an incident into an authority alert.
    """

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

    alert_id = f"ALT-{uuid4().hex[:8].upper()}"

    priority = (
        incident.get("priority")
        or calculate_priority(incident)
    )

    alert = {
        "alert_id": alert_id,
        "incident_id": incident_id,
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
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    # Assign the responsible department.
    dispatch = create_dispatch(alert)

    alert["department"] = dispatch["department"]
    alert["assigned_team"] = dispatch["assigned_team"]

    # Store alert temporarily.
    ALERTS.append(alert)

    return alert


def process_incident(incident: dict) -> dict:
    """
    Complete authority workflow:

    Incident
       ↓
    Alert
       ↓
    Department Assignment
       ↓
    Notification
    """

    alert = create_alert(incident)

    notification = send_notification(alert)

    return {
        "alert": alert,
        "notification": notification,
    }


def get_all_alerts() -> list:
    """
    Return all authority alerts.
    """

    return ALERTS


def get_alert_by_id(alert_id: str):
    """
    Find an alert using its alert ID.
    """

    for alert in ALERTS:
        if alert["alert_id"] == alert_id:
            return alert

    return None


def update_alert_status(alert_id: str, status: str):
    """
    Update the action status of an alert.

    Allowed statuses:
    PENDING_ACTION
    IN_PROGRESS
    RESOLVED
    REJECTED
    """

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

    alert["status"] = status
    alert["updated_at"] = datetime.now(timezone.utc).isoformat()

    return alert