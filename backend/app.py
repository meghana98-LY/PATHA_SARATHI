from flask import Flask
from flask_cors import CORS
from backend.database.connection import init_db
from backend.routes.incidents import incidents_bp
from backend.routes.reports import reports_bp
from backend.routes.alerts import alerts_bp

app = Flask(__name__)
CORS(app)

# Sync database schema on startup
init_db()

# Register API blueprints
app.register_blueprint(incidents_bp)
app.register_blueprint(reports_bp)
app.register_blueprint(alerts_bp)

@app.route("/health", methods=["GET"])
def health_check():
    return {"status": "HEALTHY", "service": "PATHA_SARATHI Backend API"}, 200

if __name__ == "__main__":
    print("[INFO] Starting PATHA_SARATHI Backend API Server...")
    app.run(host="0.0.0.0", port=5000, debug=True)