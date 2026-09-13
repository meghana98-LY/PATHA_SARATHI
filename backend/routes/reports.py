from flask import Blueprint, request, jsonify
from datetime import datetime, timezone
from backend.services.deduplication import process_hazard_deduplication
from backend.database.connection import get_db_connection

reports_bp = Blueprint("reports", __name__)

@reports_bp.route("/api/reports/citizen", methods=["POST"])
def submit_citizen_report():
    """
    Accepts manual road hazard reports from the citizen mobile app.
    """
    data = request.get_json()
    if not data or "latitude" not in data or "longitude" not in data:
        return jsonify({"error": "Missing latitude or longitude in report"}), 400

    hazard_type = data.get("hazard_type", "Pothole")
    latitude = float(data["latitude"])
    longitude = float(data["longitude"])
    user_id = data.get("user_id", "ANONYMOUS_CITIZEN")
    notes = data.get("notes", "")

    # Run through spatial deduplication pipeline
    result = process_hazard_deduplication(
        hazard_type=hazard_type,
        latitude=latitude,
        longitude=longitude,
        confidence=0.75  # Default confidence score for human reports
    )

    return jsonify({
        "status": "SUCCESS",
        "message": "Citizen report recorded successfully",
        "deduplication_result": result
    }), 201


@reports_bp.route("/api/reports/upvote/<int:incident_id>", methods=["POST"])
def upvote_incident(incident_id):
    """
    Allows citizens to confirm/upvote an existing hazard to elevate its priority.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM incidents WHERE id = ?", (incident_id,))
    incident = cursor.fetchone()

    if not incident:
        conn.close()
        return jsonify({"error": "Incident not found"}), 404

    new_count = incident["report_count"] + 1
    now_iso = datetime.now(timezone.utc).isoformat()

    cursor.execute("""
        UPDATE incidents 
        SET report_count = ?, last_updated_at = ? 
        WHERE id = ?
    """, (new_count, now_iso, incident_id))

    conn.commit()
    conn.close()

    return jsonify({
        "status": "SUCCESS",
        "incident_id": incident_id,
        "updated_report_count": new_count
    }), 200