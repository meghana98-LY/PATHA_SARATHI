"""
Edge Pipeline Orchestrator for PATHA SARATHI.
Wires: CameraCapture -> Frame Skip -> Detector -> Cooldown Filter -> GPS -> Evidence Packaging -> Backend Dispatch.
Includes abstract Detector interface, MockDetector, and runnable CLI.
"""

from __future__ import annotations
from edge_ai.detector import KishorDetector as kDetector
import argparse
import logging
import sys
from abc import ABC, abstractmethod
from typing import Any

import numpy as np
import requests

from edge_ai.camera_capture import CameraCapture
from edge_ai.config import EdgeConfig, config as default_config
from edge_ai.evidence_packager import EvidencePackager
from edge_ai.gps_handler import GPSHandler

# Configure structured console logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("PATHA_SARATHI_EDGE")


class BaseDetector(ABC):
    """
    Abstract AI Road-Hazard Detector interface.
    Kishor will implement this class to plug in the real YOLOv8/v11 model.
    """

    @abstractmethod
    def detect(self, frame: np.ndarray) -> list[dict[str, Any]]:
        """
        Executes road-hazard inference on a single BGR video frame.

        Args:
            frame: OpenCV numpy array (BGR).

        Returns:
            list[dict]: List of detected objects, each with:
                - 'class' (str): e.g. 'pothole', 'damaged road', 'road obstruction'
                - 'confidence' (float): 0.0 to 1.0
                - 'bbox' (list[int]): Optional bounding box coordinates [x, y, w, h] or [x1, y1, x2, y2]
        """
        pass


class MockDetector(BaseDetector):
    """
    Simulated detector producing sample hazard detections for testing and standalone operation.
    Triggers simulated detections periodically (e.g. every 10 frames) so the full pipeline
    can be validated end-to-end without deep learning dependencies or GPU.
    """

    def __init__(self, sample_detections: list[dict[str, Any]] | None = None) -> None:
        self.sample_detections = sample_detections or [
            {"class": "pothole", "confidence": 0.91, "bbox": [100, 120, 300, 250]},
            {"class": "damaged road", "confidence": 0.84, "bbox": [150, 200, 280, 180]},
            {"class": "road obstruction", "confidence": 0.95, "bbox": [220, 180, 160, 220]},
        ]
        self._call_count: int = 0

    def detect(self, frame: np.ndarray) -> list[dict[str, Any]]:
        """
        Generates simulated hazard detections periodically.
        """
        self._call_count += 1
        # Emit a detection on specific call cycles to simulate real-world intermittent hazard detection
        if self._call_count % 3 == 0:
            sample_idx = (self._call_count // 3) % len(self.sample_detections)
            detection = self.sample_detections[sample_idx].copy()
            logger.info(
                f"[AI] {detection['class']} detected (confidence={detection['confidence']:.2f}, bbox={detection.get('bbox')})"
            )
            return [detection]

        return []


class CooldownTracker:
    """
    Tracks recent hazard detections across frames to prevent duplicate incidents
    for the same physical hazard within a spatial-temporal window.
    Key: (hazard_class, round(latitude, 4), round(longitude, 4))
    """

    def __init__(self, cooldown_frames: int = 30) -> None:
        self.cooldown_frames = cooldown_frames
        self._last_seen: dict[tuple[str, float, float], int] = {}

    def should_suppress(
        self,
        hazard_class: str,
        lat: float,
        lon: float,
        current_frame: int,
    ) -> bool:
        """
        Checks if a hazard at this location was already reported within the cooldown window.

        Args:
            hazard_class: Name of the hazard.
            lat: Current latitude.
            lon: Current longitude.
            current_frame: Current frame number.

        Returns:
            bool: True if suppressed (duplicate in cooldown), False if valid new incident.
        """
        if self.cooldown_frames <= 0:
            return False

        # Key quantized to 4 decimal places (~11 meters)
        key = (hazard_class.strip().lower(), round(lat, 4), round(lon, 4))
        last_frame = self._last_seen.get(key)

        if last_frame is not None and (current_frame - last_frame) < self.cooldown_frames:
            logger.debug(
                f"[AI] Suppressed {hazard_class} due to cooldown "
                f"(last_frame={last_frame}, current={current_frame}, diff={current_frame - last_frame})"
            )
            return True

        self._last_seen[key] = current_frame
        return False


class EdgePipeline:
    """
    Main orchestrator for the PATHA SARATHI Edge Capture Module.
    Connects Camera -> Pluggable Detector -> GPS -> Evidence Packager -> Backend.
    """

    def __init__(
        self,
        camera: CameraCapture,
        detector: BaseDetector,
        gps: GPSHandler,
        packager: EvidencePackager,
        cfg: EdgeConfig | None = None,
        no_upload: bool = False,
    ) -> None:
        self.camera = camera
        self.detector = detector
        self.gps = gps
        self.packager = packager
        self.cfg = cfg or default_config
        self.no_upload = no_upload
        self.cooldown = CooldownTracker(cooldown_frames=self.cfg.DETECTION_COOLDOWN_FRAMES)

    def upload_incident(self, incident: dict[str, Any]) -> bool:
        """
        Dispatches incident JSON to Lohith's backend ingestion endpoint:
        POST /api/incidents/ingest.
        Never crashes the edge capture pipeline on network errors or backend downtime.

        Args:
            incident: Validated incident dictionary.

        Returns:
            bool: True if backend confirmed ingestion, False otherwise.
        """
        if self.no_upload:
            logger.debug(
                f"[BACKEND] Upload skipped (--no-upload enabled) "
                f"for device {incident.get('device_id', 'UNKNOWN_DEVICE')}"
            )
            return False

        url = f"{self.cfg.BACKEND_URL}/api/incidents/ingest"
        logger.info(
            f"[BACKEND] POST {url} for device "
            f"{incident.get('device_id', 'UNKNOWN_DEVICE')}"
        )

        try:
            response = requests.post(
                url,
                json=incident,
                headers={"Content-Type": "application/json"},
                timeout=3.0,
            )
            if response.status_code in (200, 201, 202):
                logger.info(
                    f"[BACKEND] Success: Ingestion confirmed for device "
                    f"{incident.get('device_id', 'UNKNOWN_DEVICE')} "
                    f"(HTTP {response.status_code})"
                )
                return True
            else:
                logger.warning(
                    f"[BACKEND] Failure: Ingestion returned HTTP {response.status_code}: {response.text[:120]}"
                )
                return False
        except Exception as e:
            logger.warning(
                f"[BACKEND] Failure: Unable to reach backend at {url}: {e}. "
                f"Device {incident.get('device_id', 'UNKNOWN_DEVICE')} "
                f"payload preserved locally."
            )
            return False

    def process_frame(self, frame_data: dict[str, Any]) -> list[dict[str, Any]]:
        """
        Processes a single frame:
        1. Frame-skip gating.
        2. Detection inference.
        3. Confidence filtering.
        4. Cooldown / deduplication.
        5. GPS query & evidence packaging.
        6. Backend dispatch.

        Args:
            frame_data: Dict with 'frame', 'frame_number', 'timestamp'.

        Returns:
            list[dict[str, Any]]: List of packaged incident payloads for this frame.
        """
        frame = frame_data["frame"]
        frame_num = frame_data["frame_number"]
        timestamp = frame_data["timestamp"]

        # 1. Frame Skip Check
        if frame_num % self.cfg.FRAME_SKIP != 0:
            return []

        # 2. Run pluggable detector
        raw_detections = self.detector.detect(frame)
        if not raw_detections:
            return []

        created_incidents: list[dict[str, Any]] = []

        # Acquire current GPS coordinates once per frame
        location = self.gps.get_location()

        for det in raw_detections:
            hazard_type = str(
                det.get("hazard_type", det.get("class", "unknown"))
            ).strip()

            raw_class = str(
                det.get("raw_class", det.get("class", "unknown"))
            ).strip()

            confidence = float(det.get("confidence", 0.0))
            # 3. Confidence Threshold Filter
            if confidence < self.cfg.CONFIDENCE_THRESHOLD:
                logger.debug(
                    f"[AI] Dropped {hazard_type} with low confidence {confidence:.2f} < {self.cfg.CONFIDENCE_THRESHOLD}"
                )
                continue

            # 4. Cooldown Deduplication Filter
            if self.cooldown.should_suppress(
                hazard_class=hazard_type,
                lat=location["latitude"],
                lon=location["longitude"],
                current_frame=frame_num,
            ):
                continue

            # 5. Evidence Packaging (Annotate image, build JSON, save locally)
            incident = self.packager.package_incident(
                frame=frame,
                detection=det,
                location=location,
                timestamp=timestamp,
            )
            backend_payload = {
                "device_id": self.cfg.BUS_ID,
                "timestamp": timestamp,
                "location": {
                    "latitude": location["latitude"],
                    "longitude": location["longitude"],
                    "speed_kmh": location.get("speed_kmh", 0.0),
                },
                "detections_count": 1,
                "hazards": [
                    {
                        "hazard_type": hazard_type,
                        "raw_class": raw_class,
                        "confidence": confidence,
                        "bbox": det.get("bbox", []),
                    }
                ],
            }
            created_incidents.append(incident)

            # 6. Backend API Upload (Non-blocking failure)
            self.upload_incident(backend_payload)

        return created_incidents

    def run(self, max_frames: int | None = None) -> int:
        """
        Executes continuous processing loop until video ends or max_frames is reached.

        Args:
            max_frames: Optional upper limit on processed frames (useful for tests/demos).

        Returns:
            int: Total number of incidents created during this execution run.
        """
        logger.info(f"[EDGE] Starting pipeline on source={self.camera.source} (BUS_ID={self.cfg.BUS_ID})")

        if not self.camera.start():
            logger.error(f"[EDGE] Aborting: Unable to open camera source '{self.camera.source}'.")
            return 0

        total_incidents = 0
        frames_seen = 0

        try:
            while True:
                if max_frames is not None and frames_seen >= max_frames:
                    logger.info(f"[EDGE] Reached requested max_frames limit: {max_frames}")
                    break

                frame_data = self.camera.read_frame()
                if frame_data is None:
                    logger.info("[EDGE] End of video stream or camera feed closed.")
                    break

                frames_seen += 1
                incidents = self.process_frame(frame_data)
                total_incidents += len(incidents)

        except KeyboardInterrupt:
            logger.info("[EDGE] Execution interrupted by user.")
        finally:
            self.camera.release()
            logger.info(
                f"[EDGE] Pipeline finished. Frames evaluated: {frames_seen}, Incidents created: {total_incidents}"
            )

        return total_incidents


def build_cli_parser() -> argparse.ArgumentParser:
    """Builds command line arguments parser for edge capture module."""
    parser = argparse.ArgumentParser(
        description="PATHA SARATHI - Edge Camera & AI Hazard Capture Module"
    )
    parser.add_argument(
        "--source",
        type=str,
        default=None,
        help="Webcam index (e.g. 0), video file path, or 'mock' for synthetic frames.",
    )
    parser.add_argument(
        "--bus-id",
        type=str,
        default=None,
        help="Identifier for the bus unit (e.g. BUS_101).",
    )
    parser.add_argument(
        "--frame-skip",
        type=int,
        default=None,
        help="Process every Nth frame (default from config/env: 5).",
    )
    parser.add_argument(
        "--confidence",
        type=float,
        default=None,
        help="Minimum detection confidence threshold (0.0 - 1.0).",
    )
    parser.add_argument(
        "--cooldown",
        type=int,
        default=None,
        help="Cooldown in frames to suppress duplicate hazard alerts.",
    )
    parser.add_argument(
        "--no-upload",
        action="store_true",
        help="Skip POSTing incidents to backend API (saves locally only).",
    )
    parser.add_argument(
        "--max-frames",
        type=int,
        default=None,
        help="Maximum frames to process before stopping (useful for testing).",
    )
    return parser


def main() -> None:
    """CLI entry point for running the module directly."""
    parser = build_cli_parser()
    args = parser.parse_args()

    # Determine runtime config
    cfg = default_config

    source = args.source if args.source is not None else cfg.VIDEO_SOURCE
    bus_id = args.bus_id if args.bus_id is not None else cfg.BUS_ID
    frame_skip = args.frame_skip if args.frame_skip is not None else cfg.FRAME_SKIP
    confidence = args.confidence if args.confidence is not None else cfg.CONFIDENCE_THRESHOLD
    cooldown = args.cooldown if args.cooldown is not None else cfg.DETECTION_COOLDOWN_FRAMES

    # Instantiate runtime config overrides if CLI flags specified
    active_cfg = EdgeConfig(
        BUS_ID=bus_id,
        VIDEO_SOURCE=source,
        FRAME_SKIP=frame_skip,
        CONFIDENCE_THRESHOLD=confidence,
        DETECTION_COOLDOWN_FRAMES=cooldown,
        GPS_MODE=cfg.GPS_MODE,
        GPS_EXHAUSTION_BEHAVIOR=cfg.GPS_EXHAUSTION_BEHAVIOR,
        BACKEND_URL=cfg.BACKEND_URL,
        OUTPUT_DIR=cfg.OUTPUT_DIR,
    )

    camera = CameraCapture(source=active_cfg.VIDEO_SOURCE)
    detector = kDetector()
    gps = GPSHandler(
        mode=active_cfg.GPS_MODE,
        exhaustion_behavior=active_cfg.GPS_EXHAUSTION_BEHAVIOR,
    )
    packager = EvidencePackager(cfg=active_cfg)

    pipeline = EdgePipeline(
        camera=camera,
        detector=detector,
        gps=gps,
        packager=packager,
        cfg=active_cfg,
        no_upload=args.no_upload,
    )

    incidents_count = pipeline.run(max_frames=args.max_frames)
    sys.exit(0 if incidents_count >= 0 else 1)


if __name__ == "__main__":
    main()
