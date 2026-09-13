# PATHA SARATHI - Edge Capture Module

The **Edge Capture Module** is responsible for onboard bus telemetry and video capture: reading road video feeds, simulating or reading GPS location, passing frames to a pluggable AI hazard detector, suppressing consecutive duplicates with a lightweight cooldown filter, saving annotated evidence frames, generating standardized Incident JSON records, and optionally dispatching them to the backend API.

---

## Architecture & Flow

```
CameraCapture (Webcam / Video File / Mock)
      ↓
Frame Skip (e.g. process every 5th frame)
      ↓
Pluggable Detector Interface (BaseDetector)
  ├── MockDetector (active now for testing)
  └── Kishor's YOLO Detector (drop-in replacement)
      ↓
Confidence Threshold Filter (drops < CONFIDENCE_THRESHOLD)
      ↓
Cooldown / Deduplication Filter (hazard + ~11m quantized GPS bucket)
      ↓
GPSHandler (Simulation Route or Real NMEA Hardware Adapter)
      ↓
EvidencePackager
  ├── Draws bounding box & class label overlay
  ├── Generates persistent monotonic Incident ID (INC-XXXX)
  ├── Saves annotated JPEG -> data/evidence/INC-XXXX.jpg
  └── Saves JSON -> data/test_data/INC-XXXX.json
      ↓
Backend Ingestion Dispatch (POST /api/incidents)
  └── Fails safely if offline; camera pipeline keeps running uninterrupted
```

---

## Installation

### Prerequisites
- Python 3.11+
- Virtual environment (recommended)

### Setup
```bash
# Clone and enter directory
cd PATHA-SARATHI

# Install dependencies
pip install -r requirements.txt

# Create environment configuration from template
cp .env.example .env
```

---

## Running the Module

### Standalone Mock Run (No Hardware Required)
You can run the full edge pipeline immediately without any camera, GPU, or backend:
```bash
python -m edge_ai.edge_pipeline --source mock --max-frames 30 --no-upload
```

### Run with a Prerecorded Route Video
Place your route video at `data/sample_videos/bus_route.mp4`:
```bash
python -m edge_ai.edge_pipeline --source data/sample_videos/bus_route.mp4 --bus-id BUS_101
```

### Run with Live Webcam
```bash
python -m edge_ai.edge_pipeline --source 0 --frame-skip 5 --confidence 0.6
```

### CLI Arguments
| Flag | Description | Default |
|---|---|---|
| `--source` | Camera index (e.g. `0`), video file path, or `'mock'` | From `VIDEO_SOURCE` in `.env` |
| `--bus-id` | Bus identifier string (e.g. `BUS_101`) | From `BUS_ID` in `.env` |
| `--frame-skip` | Process every Nth frame | From `FRAME_SKIP` (5) |
| `--confidence`| Minimum confidence threshold (0.0 - 1.0) | From `CONFIDENCE_THRESHOLD` (0.50) |
| `--cooldown` | Cooldown in frames for deduplication | From `DETECTION_COOLDOWN_FRAMES` (30) |
| `--no-upload` | Disables HTTP POST to backend | False |
| `--max-frames`| Terminate after N frames (useful for test runs) | Unlimited |

---

## GPS Simulation

`GPSHandler` provides coordinates via interchangeable adapters:
- **`simulation` mode**: Cycles through a configured list of Bangalore route coordinates. On route completion, behavior is governed by `GPS_EXHAUSTION_BEHAVIOR`:
  - `loop` (default): Loops seamlessly back to the start of the route.
  - `hold`: Retains the final terminal coordinate.
- **`real` mode**: Outlines a drop-in hardware adapter (`RealGPSAdapter`) ready for serial NMEA USB GPS dongles without touching pipeline code.

---

## How Kishor Plugs in His YOLO Detector

Kishor's detector only needs to inherit from `BaseDetector` in `edge_ai/edge_pipeline.py`:

```python
import cv2
import numpy as np
from edge_ai.edge_pipeline import BaseDetector
from ultralytics import YOLO  # when ready

class KishorYoloDetector(BaseDetector):
    def __init__(self, model_path: str = "models/best.pt"):
        self.model = YOLO(model_path)

    def detect(self, frame: np.ndarray) -> list[dict]:
        results = self.model(frame, verbose=False)
        detections = []
        for r in results:
            for box in r.boxes:
                cls_id = int(box.cls[0])
                cls_name = self.model.names[cls_id]
                conf = float(box.conf[0])
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                detections.append({
                    "class": cls_name,
                    "confidence": conf,
                    "bbox": [int(x1), int(y1), int(x2), int(y2)]
                })
        return detections
```

To use it in `edge_ai/edge_pipeline.py`, change:
```python
detector = KishorYoloDetector()  # replaces MockDetector()
```
Zero modifications are needed in `camera_capture.py`, `gps_handler.py`, or `evidence_packager.py`.

---

## How Lohith's Backend Ingestion Plugs In

- The pipeline issues an HTTP `POST` request to `{BACKEND_URL}/api/incidents`.
- Configured via `BACKEND_URL` in `.env` (default: `http://localhost:8000`).
- If the backend is unreachable or returns an error, the error is logged as a warning, local JSON is preserved under `data/test_data/INC-XXXX.json`, and the video feed continues uninterrupted.

---

## Incident JSON Schema (The Contract)

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

### Contract Fields:
- `incident_id`: Persistent unique ID formatted as `INC-XXXX`. Reconciled against existing files on reboot.
- `type`: Lowercase hazard label (`pothole`, `damaged road`, `road obstruction`, `missing road sign`, `damaged divider`).
- `confidence`: Detection confidence (0.00 to 1.00).
- `latitude` & `longitude`: Float GPS coordinates.
- `timestamp`: UTC ISO-8601 with trailing `Z`.
- `image_url`: Forward-slash relative path to annotated frame.
- `source`: `"bus"`.
- `bus_id`: Configurable bus identifier.
- `status`: `"pending"`.
- `priority`: Mapped priority level (`critical`, `high`, `medium`).
