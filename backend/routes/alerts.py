from flask import Blueprint, request, jsonify
from backend.database.connection import get_db_connection
from backend.services.deduplication import haversine_distance
from backend.services.prioritization import calculate_priority_score
from backend.config import Config

alerts_bp = Blueprint("alerts", __name__)

@alerts_bp.route("/api/alerts/proximity", methods=["GET"])
def get_proximity_alerts():
    try:
        user_lat = float(request.args.get("lat"))
        user_lng = float(request.args.get("lng"))
    except (TypeError, ValueError):
        return jsonify({"error": "Valid 'lat' and 'lng' query parameters required"}), 400

    alert_radius = Config.PROXIMITY_ALERT_RADIUS_METERS

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM incidents WHERE status != 'RESOLVED'")
    incidents = cursor.fetchall()
    conn.close()

    active_alerts = []

    for incident in incidents:
        dist = haversine_distance(user_lat, user_lng, incident["latitude"], incident["longitude"])
        if dist <= alert_radius:
            score = calculate_priority_score(
                hazard_type=incident["hazard_type"],
                confidence=incident["confidence"],
                report_count=incident["report_count"]
            )
            
            if score >= 40.0:
                active_alerts.append({
                    "incident_id": incident["id"],
                    "hazard_type": incident["hazard_type"],
                    "distance_meters": round(dist, 1),
                    "priority_score": score,
                    "warning_level": "HIGH" if score >= Config.HIGH_RISK_PRIORITY_SCORE else "MEDIUM"
                })

    return jsonify({"alerts_count": len(active_alerts), "alerts": active_alerts}), 200