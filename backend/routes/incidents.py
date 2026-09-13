from datetime import datetime, timezone
from flask import Blueprint, request, jsonify
from backend.services.deduplication import process_hazard_deduplication
from backend.database.connection import get_db_connection

incidents_bp = Blueprint("incidents", __name__)

VALID_STATUSES = {"pending", "in_progress", "verified", "resolved"}

@incidents_bp.route("/api/incidents/ingest", methods=["POST"])
def ingest_edge_payload():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid or missing JSON payload"}), 400

    device_id = data.get("device_id", "UNKNOWN_DEVICE")
    timestamp = data.get("timestamp")
    location = data.get("location", {})
    hazards = data.get("hazards", [])

    if not hazards:
        return jsonify({"error": "No hazards present in payload"}), 400

    # Process the primary hazard in the list
    hazard = hazards[0]

    result = process_hazard_deduplication(
        device_id=device_id,
        timestamp=timestamp,
        location=location,
        hazard=hazard
    )

    return jsonify(result), 200

@incidents_bp.route("/api/incidents", methods=["GET"])
def get_active_incidents():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM incidents WHERE status != 'RESOLVED' ORDER BY priority_score DESC")
    rows = cursor.fetchall()
    conn.close()

    incidents = [dict(row) for row in rows]
    return jsonify({"incidents": incidents}), 200

@incidents_bp.route("/api/incidents/<int:incident_id>/status", methods=["PATCH"])
def update_incident_status(incident_id):
    data = request.get_json()
    if not data or "status" not in data:
        return jsonify({"error": "Missing 'status' field in JSON request payload"}), 400

    raw_status = data.get("status")
    if not isinstance(raw_status, str):
        return jsonify({"error": "Field 'status' must be a string"}), 400

    normalized_status = raw_status.strip().lower()
    if normalized_status not in VALID_STATUSES:
        return jsonify({
            "error": f"Invalid status '{raw_status}'. Must be one of: {', '.join(sorted(VALID_STATUSES))}"
        }), 400

    db_status = normalized_status.upper()
    now_iso = datetime.now(timezone.utc).isoformat()

    conn = get_db_connection()
    cursor = conn.cursor()

    # Verify incident exists
    cursor.execute("SELECT id FROM incidents WHERE id = ?", (incident_id,))
    incident = cursor.fetchone()
    if not incident:
        conn.close()
        return jsonify({"error": f"Incident with ID {incident_id} not found"}), 404

    # Update status and timestamp in SQLite database
    cursor.execute("""
        UPDATE incidents 
        SET status = ?, last_updated_at = ? 
        WHERE id = ?
    """, (db_status, now_iso, incident_id))

    conn.commit()
    conn.close()

    return jsonify({
        "success": True,
        "incident_id": incident_id,
        "status": normalized_status,
        "message": f"Incident {incident_id} status updated to '{normalized_status}'"
    }), 200
