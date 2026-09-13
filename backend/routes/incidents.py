from flask import Blueprint, request, jsonify
from backend.services.deduplication import process_hazard_deduplication
from backend.database.connection import get_db_connection

incidents_bp = Blueprint("incidents", __name__)

@incidents_bp.route("/api/incidents/ingest", methods=["POST"])
def ingest_edge_payload():
    payload = request.get_json()
    if not payload or "hazards" not in payload:
        return jsonify({"error": "Invalid payload format"}), 400

    lat = payload["location"]["latitude"]
    lng = payload["location"]["longitude"]
    processed_results = []

    for hazard in payload["hazards"]:
        res = process_hazard_deduplication(
            hazard_type=hazard["hazard_type"],
            latitude=lat,
            longitude=lng,
            confidence=hazard["confidence"]
        )
        processed_results.append(res)

    return jsonify({
        "status": "SUCCESS",
        "processed_count": len(processed_results),
        "results": processed_results
    }), 201

@incidents_bp.route("/api/incidents", methods=["GET"])
def get_all_incidents():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM incidents ORDER BY last_updated_at DESC")
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify({"incidents": rows}), 200