from flask import Flask
from flask_cors import CORS
from backend.routes.incidents import incidents_bp

app = Flask(__name__)
CORS(app)  # Enables cross-origin requests for Frontend and Mobile apps

app.register_blueprint(incidents_bp)

@app.route("/health", methods=["GET"])
def health_check():
    return {"status": "HEALTHY", "service": "PATHA_SARATHI Backend API"}, 200

if __name__ == "__main__":
    print("[INFO] Starting PATHA_SARATHI Backend API Server...")
    app.run(host="0.0.0.0", port=5000, debug=True)