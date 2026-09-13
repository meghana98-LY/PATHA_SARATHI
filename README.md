# PATHA SARATHI - Smart Road Hazard Detection & Reporting System

**PATHA SARATHI** is an automated, edge-to-cloud road hazard monitoring system built for the Smart India Hackathon. It mounts intelligent capture units on public transit buses to passively record road surfaces, detect hazards (potholes, road damage, obstructions), geolocate incidents via GPS, package visual evidence, and transmit verified telemetry to municipal authorities via an interactive GIS dashboard.

---

## Overall System Pipeline

```
BUS CAMERA
    ↓
FRAME CAPTURE  (Edge AI Module - Namith)
    ↓
AI ROAD-HAZARD DETECTION  (Kishor - YOLOv8/v11)
    ↓
GPS + TIMESTAMP ACQUISITION  (Edge AI Module - Namith)
    ↓
EVIDENCE PACKAGING (JSON + Image)  (Edge AI Module - Namith)
    ↓
BACKEND INGESTION API  (Lohith - FastAPI/Express)
    ↓
SPATIAL-TEMPORAL DEDUPLICATION & VERIFICATION  (Lohith)
    ↓
CENTRAL DATABASE  (PostgreSQL / PostGIS)
    ↓
GIS DASHBOARD & HEATMAPS  (Parvati)
    ↓
MUNICIPAL AUTHORITY ACTION
```

---

## Role of This Module: Bus Camera + GPS + Edge Capture

This repository houses the **Edge Capture Module** owned by **Namith**.
It operates directly on the bus edge device and is strictly responsible for:
1. Video acquisition (webcam, route video file, or synthetic mock).
2. Frame skipping and sampling.
3. Pluggable road-hazard detector interface (`BaseDetector`) currently powered by `MockDetector`, ready for Kishor's YOLO detector.
4. Edge-side lightweight cooldown deduplication (prevents consecutive frame alerts for the same physical hazard).
5. GPS location acquisition (simulated Bangalore route or real NMEA hardware).
6. Evidence image rendering (bounding box overlays) saved to `data/evidence/INC-XXXX.jpg`.
7. Standardized Incident JSON generation saved locally to `data/test_data/INC-XXXX.json`.
8. Fault-tolerant HTTP POST dispatch to Lohith's backend (`/api/incidents`).

---

## Project Structure

```
PATHA-SARATHI/
├── edge_ai/
│   ├── __init__.py               # Edge AI package definition
│   ├── camera_capture.py         # VideoCapture wrapper (webcam, file, mock)
│   ├── gps_handler.py            # Simulated & real GPS adapter
│   ├── evidence_packager.py      # Bounding box rendering & JSON packaging
│   ├── edge_pipeline.py          # Pipeline orchestrator & CLI
│   ├── config.py                 # Central configuration and path handling
│   └── README.md                 # Detailed module technical documentation
├── data/
│   ├── sample_videos/            # Directory for prerecorded bus route mp4 files
│   ├── sample_images/            # Directory for test frames
│   ├── test_data/                # Local incident JSON files (INC-XXXX.json)
│   └── evidence/                 # Annotated evidence images (INC-XXXX.jpg)
├── tests/
│   └── test_edge_pipeline.py     # 19 comprehensive pytest unit & integration tests
├── requirements.txt              # Minimal project dependencies
├── .env.example                  # Environment variable configuration template
├── .gitignore                    # Secrets and build ignore rules
├── conftest.py                   # Pytest path resolution
└── README.md                     # Project overview and system context
```

---

## Quick Start

### 1. Setup Environment
```bash
# Install dependencies
pip install -r requirements.txt

# Copy environment variables
cp .env.example .env
```

### 2. Run the Edge Pipeline (Standalone Mock Mode)
Runs immediately without needing a physical camera, GPS, or backend:
```bash
python -m edge_ai.edge_pipeline --source mock --max-frames 20 --no-upload
```

### 3. Run with a Bus Video File
Place your route video at `data/sample_videos/bus_route.mp4` and run:
```bash
python -m edge_ai.edge_pipeline --source data/sample_videos/bus_route.mp4 --bus-id BUS_101
```

### 4. Run Automated Test Suite
```bash
pytest
```
All 19 tests run offline without hardware dependencies.

---

## Team Integration Contracts

- **Kishor (AI / YOLO)**: Implements `BaseDetector.detect(frame) -> list[dict]`. See [`edge_ai/README.md`](edge_ai/README.md) for code template.
- **Lohith (Backend)**: Ingestion endpoint receives `POST /api/incidents`. See Incident JSON contract specification below.
- **Parvati (GIS Dashboard)**: Visualizes incidents using latitude, longitude, type, priority, and annotated evidence image URL.

### Standard Incident JSON Contract
```json
{
  "incident_id": "INC-0001",
  "type": "pothole",
  "confidence": 0.91,
  "latitude": 12.9716,
  "longitude": 77.5946,
  "timestamp": "2026-09-12T10:30:20Z",
  "image_url": "data/evidence/INC-0001.jpg",
  "source": "bus",
  "bus_id": "BUS_101",
  "status": "pending",
  "priority": "high"
}
```
