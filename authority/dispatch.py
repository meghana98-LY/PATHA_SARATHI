# authority/dispatch.py

"""
PATHA SARATHI - Authority Dispatch Module

Responsible for assigning road incidents to
the appropriate municipal department.
"""


# Hazard type → Responsible department
DEPARTMENT_MAPPING = {
    "pothole": "Road Maintenance",
    "damaged road": "Road Maintenance",
    "road obstruction": "Road Maintenance",
    "damaged divider": "Road Infrastructure",
    "missing road sign": "Traffic Management",
    "waterlogging": "Drainage Department",
    "streetlight failure": "Electrical Department",
}


def assign_department(hazard_type: str) -> str:
    """
    Assign a department based on the hazard type.

    Example:
        assign_department("Pothole")
        → "Road Maintenance"
    """

    if not hazard_type:
        return "General Municipal Maintenance"

    normalized_type = hazard_type.lower().strip()

    return DEPARTMENT_MAPPING.get(
        normalized_type,
        "General Municipal Maintenance"
    )


def create_dispatch(incident: dict) -> dict:
    """
    Create a dispatch record for an incident.
    """

    hazard_type = (
        incident.get("hazard_type")
        or incident.get("type")
        or "unknown"
    )

    department = assign_department(hazard_type)

    return {
        "incident_id": (
            incident.get("incident_code")
            or incident.get("incident_id")
        ),
        "department": department,
        "assigned_team": f"{department} Team",
        "dispatch_status": "PENDING",
    }