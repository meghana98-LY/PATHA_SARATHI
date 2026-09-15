from flask import Flask
from flask_cors import CORS
from backend.database.connection import init_db
from backend.routes.incidents import incidents_bp
from backend.routes.reports import reports_bp
from backend.routes.alerts import alerts_bp

app = Flask(__name__)
CORS(app)

# Synchronize NeonDB PostgreSQL tables on launch
init_db()

app.register_blueprint(incidents_bp)
app.register_blueprint(reports_bp)
app.register_blueprint(alerts_bp)

@app.route("/health", methods=["GET"])
def health():
    return {"status": "HEALTHY", "service": "PATHA_SARATHI Backend API"}, 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)