from flask import Blueprint, request, jsonify
from backend.services.deduplication import process_hazard_deduplication
from backend.database.connection import get_db_connection

incidents_bp = Blueprint("incidents", __name__)

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
    
    # Ensure all fields including image_data are retrieved
    cursor.execute("""
        SELECT id, incident_code, hazard_type, latitude, longitude, 
               priority_score, confidence, report_count, verification_status, 
               status, image_data, first_reported_at, last_updated_at
        FROM incidents 
        WHERE status != 'RESOLVED' 
        ORDER BY priority_score DESC
    """)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    incidents = [dict(row) for row in rows]
    return jsonify({"incidents": incidents}), 200