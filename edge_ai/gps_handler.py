import random
from datetime import datetime, timezone

def get_current_location():
    """
    Returns spatial metadata (latitude, longitude, speed) and ISO timestamp.
    Simulates real-time edge vehicle GPS feed for development.
    """
    base_lat = 12.9716  # Bengaluru coordinates baseline
    base_lng = 77.5946

    # Add minor variation to simulate moving vehicle
    current_lat = base_lat + random.uniform(-0.005, 0.005)
    current_lng = base_lng + random.uniform(-0.005, 0.005)

    return {
        "latitude": round(current_lat, 6),
        "longitude": round(current_lng, 6),
        "speed_kmh": round(random.uniform(20.0, 45.0), 2),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }