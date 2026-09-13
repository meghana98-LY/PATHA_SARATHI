import json
from edge_ai.gps_handler import get_current_location

def package_evidence(detections, device_id="EDGE_BUS_NODE_01"):
    """
    Combines YOLO detections, GPS coordinates, and device metadata into 
    the standardized JSON structure consumed by Lohith's backend API.
    """
    gps_data = get_current_location()

    payload = {
        "device_id": device_id,
        "timestamp": gps_data["timestamp"],
        "location": {
            "latitude": gps_data["latitude"],
            "longitude": gps_data["longitude"],
            "speed_kmh": gps_data["speed_kmh"]
        },
        "detections_count": len(detections),
        "hazards": detections
    }

    return payload

if __name__ == "__main__":
    from edge_ai.detector import RoadHazardDetector

    # Complete pipeline integration test
    detector = RoadHazardDetector()
    
    # Run mock detection output
    mock_detections = [
        {
            "hazard_type": "Pothole",
            "raw_class": "D40",
            "confidence": 0.89,
            "bbox": [120.5, 230.1, 310.2, 450.0]
        }
    ]

    payload = package_evidence(mock_detections)
    print("\n--- Kishor's Integrated Edge AI JSON Payload ---")
    print(json.dumps(payload, indent=2))