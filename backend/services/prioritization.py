HAZARD_SEVERITY_WEIGHTS = {
    "Pothole": 40,
    "Alligator Crack": 30,
    "Transverse Crack": 20,
    "Longitudinal Crack": 10,
    "General Road Damage": 25
}

def calculate_priority_score(hazard_type, confidence, report_count=1, speed_kmh=0.0):
    """
    Calculates dynamic hazard priority score from 0 to 100.
    """
    base_weight = HAZARD_SEVERITY_WEIGHTS.get(hazard_type, 15)
    confidence_weight = confidence * 20
    frequency_weight = min(report_count * 5, 20)
    speed_weight = 20 if speed_kmh >= 40.0 else (10 if speed_kmh >= 20.0 else 0)

    total_score = base_weight + confidence_weight + frequency_weight + speed_weight
    return min(round(total_score, 2), 100.0)