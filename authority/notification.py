# authority/notification.py

"""
PATHA SARATHI - Notification Module

Responsible for generating authority notifications.

For the prototype, notifications are simulated
through the dashboard/API and console.
"""

from datetime import datetime, timezone


def create_notification(alert: dict) -> dict:
    """
    Create a notification payload from an authority alert.
    """

    priority = alert.get("priority", "medium").upper()

    hazard_type = (
        alert.get("hazard_type")
        or alert.get("type")
        or "Unknown"
    )

    department = alert.get(
        "department",
        "General Municipal Maintenance"
    )

    latitude = alert.get("latitude")
    longitude = alert.get("longitude")

    message = (
        f"{priority} PRIORITY INCIDENT: "
        f"{hazard_type} reported at "
        f"({latitude}, {longitude}). "
        f"Assigned to {department}."
    )

    return {
        "alert_id": alert.get("alert_id"),
        "channel": "dashboard",
        "message": message,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "read": False,
    }


def send_notification(alert: dict) -> dict:
    """
    Simulate sending a notification.

    Future integrations:
    - Email
    - SMS
    - WhatsApp
    - Push notification
    """

    notification = create_notification(alert)

    print("\n========== AUTHORITY NOTIFICATION ==========")
    print(notification["message"])
    print("============================================\n")

    return notification