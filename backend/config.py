import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # NeonDB PostgreSQL Connection URI
    DATABASE_URL = os.getenv("DATABASE_URL")
    
    # Deduplication & Thresholds
    DEDUPLICATION_RADIUS_METERS = 15.0
    CONFIDENCE_THRESHOLD = 0.40
    
    # Alert Trigger Settings
    HIGH_RISK_PRIORITY_SCORE = 75.0
    PROXIMITY_ALERT_RADIUS_METERS = 100.0
    
    # App Settings
    SECRET_KEY = os.getenv("SECRET_KEY", "patha-sarathi-sih-secret-2026")
    DEBUG = True