"""
Unit and integration tests for PATHA SARATHI Edge Capture Module.
Runs completely offline without physical camera, GPS hardware, or live backend.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from edge_ai.camera_capture import CameraCapture
from edge_ai.config import EdgeConfig
from edge_ai.evidence_packager import (
    EvidencePackager,
    IncidentIdGenerator,
    get_hazard_priority,
)
from edge_ai.gps_handler import GPSHandler, SimulatedGPSAdapter
from edge_ai.edge_pipeline import (
    BaseDetector,
    CooldownTracker,
    EdgePipeline,
    MockDetector,
)


@pytest.fixture
def temp_edge_config(tmp_path: Path) -> EdgeConfig:
    """Fixture providing isolated temporary storage paths for tests."""
    data_dir = tmp_path / "data"
    cfg = EdgeConfig(
        BUS_ID="BUS_TEST",
        VIDEO_SOURCE="mock",
        FRAME_SKIP=1,
        CONFIDENCE_THRESHOLD=0.5,
        DETECTION_COOLDOWN_FRAMES=10,
        GPS_MODE="simulation",
        GPS_EXHAUSTION_BEHAVIOR="loop",
        BACKEND_URL="http://mock-backend:8000",
        OUTPUT_DIR=data_dir,
    )
    cfg.ensure_directories()
    return cfg


# ---------------------------------------------------------------------------
# 1. GPS Simulation Tests
# ---------------------------------------------------------------------------

def test_gps_simulation_advances_and_loops() -> None:
    """Tests that SimulatedGPSAdapter advances coordinates and loops when exhausted."""
    route = [
        {"latitude": 12.9716, "longitude": 77.5946},
        {"latitude": 12.9720, "longitude": 77.5950},
    ]
    gps = GPSHandler(mode="simulation", route=route, exhaustion_behavior="loop")

    p1 = gps.get_location()
    assert p1["latitude"] == 12.9716
    assert p1["longitude"] == 77.5946

    p2 = gps.get_location()
    assert p2["latitude"] == 12.9720
    assert p2["longitude"] == 77.5950

    # Test loop back to start
    p3 = gps.get_location()
    assert p3["latitude"] == 12.9716
    assert p3["longitude"] == 77.5946


def test_gps_simulation_hold_behavior() -> None:
    """Tests that exhaustion_behavior='hold' keeps the final coordinate."""
    route = [
        {"latitude": 12.9716, "longitude": 77.5946},
        {"latitude": 12.9720, "longitude": 77.5950},
    ]
    gps = GPSHandler(mode="simulation", route=route, exhaustion_behavior="hold")

    gps.get_location()  # point 1
    p2 = gps.get_location()  # point 2 (last)
    p3 = gps.get_location()  # held point 2

    assert p2 == p3
    assert p3["latitude"] == 12.9720


def test_gps_coordinate_validation() -> None:
    """Tests that out-of-range coordinates trigger error handling and safe fallback."""
    with pytest.raises(ValueError):
        SimulatedGPSAdapter(route=[{"latitude": 95.0, "longitude": 77.5946}])


# ---------------------------------------------------------------------------
# 2. Priority Calculation Tests
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "hazard,expected_priority",
    [
        ("pothole", "high"),
        ("POTHOLE", "high"),
        ("damaged road", "high"),
        ("road obstruction", "critical"),
        ("missing road sign", "medium"),
        ("damaged divider", "medium"),
        ("fallen tree", "medium"),  # unknown defaults to medium
        ("unknown", "medium"),
    ],
)
def test_priority_calculation(hazard: str, expected_priority: str) -> None:
    assert get_hazard_priority(hazard) == expected_priority


# ---------------------------------------------------------------------------
# 3. Incident ID Generation and Persistence Across Restarts
# ---------------------------------------------------------------------------

def test_incident_id_sequential_and_restart(tmp_path: Path) -> None:
    """Tests that IncidentIdGenerator starts clean, increments, and resumes after restart."""
    evidence_dir = tmp_path / "evidence"
    test_data_dir = tmp_path / "test_data"
    evidence_dir.mkdir(parents=True)
    test_data_dir.mkdir(parents=True)

    # First session
    gen1 = IncidentIdGenerator(evidence_dir, test_data_dir)
    id1 = gen1.next_id()
    id2 = gen1.next_id()
    assert id1 == "INC-0001"
    assert id2 == "INC-0002"

    # Simulate files left on disk from session 1
    (evidence_dir / "INC-0001.jpg").write_bytes(b"mock_img")
    (test_data_dir / "INC-0002.json").write_text("{}", encoding="utf-8")

    # Second session (simulating app restart)
    gen2 = IncidentIdGenerator(evidence_dir, test_data_dir)
    id3 = gen2.next_id()
    assert id3 == "INC-0003"


# ---------------------------------------------------------------------------
# 4. Evidence Packaging and JSON Schema Contract Tests
# ---------------------------------------------------------------------------

def test_evidence_packaging_contract(temp_edge_config: EdgeConfig) -> None:
    """Tests exact contract JSON schema compliance and image persistence."""
    packager = EvidencePackager(cfg=temp_edge_config)

    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    detection = {
        "class": "pothole",
        "confidence": 0.91,
        "bbox": [100, 120, 300, 250],
    }
    location = {"latitude": 12.9716, "longitude": 77.5946}
    timestamp = "2026-09-12T10:30:20Z"

    incident = packager.package_incident(
        frame=frame,
        detection=detection,
        location=location,
        timestamp=timestamp,
    )

    # Verify exact field schema (Lohith & Parvati contract)
    required_fields = [
        "incident_id",
        "type",
        "confidence",
        "latitude",
        "longitude",
        "timestamp",
        "image_url",
        "source",
        "bus_id",
        "status",
        "priority",
    ]
    for field in required_fields:
        assert field in incident, f"Missing required contract field: {field}"

    assert incident["incident_id"] == "INC-0001"
    assert incident["type"] == "pothole"
    assert incident["confidence"] == 0.91
    assert incident["latitude"] == 12.9716
    assert incident["longitude"] == 77.5946
    assert incident["timestamp"] == "2026-09-12T10:30:20Z"
    assert incident["image_url"] == "data/evidence/INC-0001.jpg"
    assert incident["source"] == "bus"
    assert incident["bus_id"] == "BUS_TEST"
    assert incident["status"] == "pending"
    assert incident["priority"] == "high"

    # Verify files on disk
    evidence_img = temp_edge_config.EVIDENCE_DIR / "INC-0001.jpg"
    assert evidence_img.exists()
    assert evidence_img.stat().st_size > 0

    local_json = temp_edge_config.TEST_DATA_DIR / "INC-0001.json"
    assert local_json.exists()
    with open(local_json, "r", encoding="utf-8") as f:
        saved_data = json.load(f)
    assert saved_data["incident_id"] == "INC-0001"


# ---------------------------------------------------------------------------
# 5. Cooldown Logic Tests
# ---------------------------------------------------------------------------

def test_cooldown_suppression() -> None:
    """Tests that CooldownTracker suppresses duplicate hazard reports within window."""
    tracker = CooldownTracker(cooldown_frames=20)

    # Frame 100: First sighting -> Not suppressed
    suppress_1 = tracker.should_suppress("pothole", 12.9716, 77.5946, current_frame=100)
    assert suppress_1 is False

    # Frame 105: Same hazard & location within 20 frames -> Suppressed
    suppress_2 = tracker.should_suppress("pothole", 12.9716, 77.5946, current_frame=105)
    assert suppress_2 is True

    # Frame 105: Different hazard class at same location -> Not suppressed
    suppress_different_class = tracker.should_suppress("road obstruction", 12.9716, 77.5946, current_frame=105)
    assert suppress_different_class is False

    # Frame 125: Same hazard after cooldown (125 - 100 = 25 >= 20) -> Not suppressed
    suppress_after_cooldown = tracker.should_suppress("pothole", 12.9716, 77.5946, current_frame=125)
    assert suppress_after_cooldown is False


# ---------------------------------------------------------------------------
# 6. Mock Detector Contract Tests
# ---------------------------------------------------------------------------

def test_mock_detector_conformance() -> None:
    """Tests that MockDetector conforms to BaseDetector and returns expected structure."""
    detector: BaseDetector = MockDetector()
    frame = np.zeros((100, 100, 3), dtype=np.uint8)

    detections: list[dict] = []
    # Call multiple times to trigger the periodic mock detection
    for _ in range(5):
        res = detector.detect(frame)
        if res:
            detections.extend(res)

    assert len(detections) > 0
    det = detections[0]
    assert "class" in det
    assert "confidence" in det
    assert 0.0 <= det["confidence"] <= 1.0


# ---------------------------------------------------------------------------
# 7. Invalid Camera Handling Tests
# ---------------------------------------------------------------------------

def test_camera_invalid_source_graceful_handling() -> None:
    """Tests that CameraCapture handles invalid file path without crashing."""
    cam = CameraCapture(source="non_existent_route_file_9999.mp4")
    success = cam.start()
    assert success is False
    assert cam.is_opened is False

    frame_data = cam.read_frame()
    assert frame_data is None

    # Safe release
    cam.release()


def test_camera_synthetic_mock_mode() -> None:
    """Tests that CameraCapture(source='mock') supplies synthetic frames."""
    cam = CameraCapture(source="mock")
    assert cam.start() is True

    frame_data = cam.read_frame()
    assert frame_data is not None
    assert frame_data["frame_number"] == 1
    assert frame_data["timestamp"].endswith("Z")
    assert frame_data["frame"].shape == (480, 640, 3)

    cam.release()


# ---------------------------------------------------------------------------
# 8. Edge Pipeline Integration and Upload Failure Resilience Tests
# ---------------------------------------------------------------------------

def test_pipeline_confidence_filtering(temp_edge_config: EdgeConfig) -> None:
    """Tests that detections below CONFIDENCE_THRESHOLD are dropped."""
    # Set high threshold
    high_conf_cfg = EdgeConfig(
        BUS_ID="BUS_TEST",
        CONFIDENCE_THRESHOLD=0.95,
        FRAME_SKIP=1,
        DETECTION_COOLDOWN_FRAMES=0,
        OUTPUT_DIR=temp_edge_config.OUTPUT_DIR,
    )

    class LowConfDetector(BaseDetector):
        def detect(self, frame: np.ndarray) -> list[dict]:
            return [{"class": "pothole", "confidence": 0.80, "bbox": None}]

    cam = CameraCapture(source="mock")
    gps = GPSHandler(mode="simulation")
    packager = EvidencePackager(cfg=high_conf_cfg)

    pipeline = EdgePipeline(
        camera=cam,
        detector=LowConfDetector(),
        gps=gps,
        packager=packager,
        cfg=high_conf_cfg,
        no_upload=True,
    )

    cam.start()
    frame_data = cam.read_frame()
    assert frame_data is not None

    incidents = pipeline.process_frame(frame_data)
    # Since confidence 0.80 < threshold 0.95, no incident should be produced
    assert len(incidents) == 0
    cam.release()


def test_backend_upload_failure_resilience(temp_edge_config: EdgeConfig) -> None:
    """Tests that upload_incident handles connection failure without raising exceptions."""
    cam = CameraCapture(source="mock")
    gps = GPSHandler(mode="simulation")
    packager = EvidencePackager(cfg=temp_edge_config)

    pipeline = EdgePipeline(
        camera=cam,
        detector=MockDetector(),
        gps=gps,
        packager=packager,
        cfg=temp_edge_config,
        no_upload=False,
    )

    mock_incident = {
        "incident_id": "INC-0001",
        "type": "pothole",
        "confidence": 0.91,
        "latitude": 12.9716,
        "longitude": 77.5946,
        "timestamp": "2026-09-12T10:30:20Z",
        "image_url": "data/evidence/INC-0001.jpg",
        "source": "bus",
        "bus_id": "BUS_TEST",
        "status": "pending",
        "priority": "high",
    }

    # Simulate backend down (connection error)
    with patch("requests.post", side_effect=Exception("Connection refused")):
        upload_result = pipeline.upload_incident(mock_incident)
        assert upload_result is False  # Fails safely without crashing
