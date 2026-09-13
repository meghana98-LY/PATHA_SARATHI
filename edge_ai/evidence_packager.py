"""
Evidence packaging module for PATHA SARATHI.
Annotates captured video frames, generates unique Incident IDs, constructs
the standard Incident JSON, and persists evidence images and metadata locally.
"""

from __future__ import annotations

import json
import logging
import re
import threading
from pathlib import Path
from typing import Any

import cv2
import numpy as np

from edge_ai.config import EdgeConfig, config as default_config

logger = logging.getLogger(__name__)

# Priority mapping for road hazard classes
PRIORITY_MAP: dict[str, str] = {
    "pothole": "high",
    "damaged road": "high",
    "road obstruction": "critical",
    "missing road sign": "medium",
    "damaged divider": "medium",
}


def get_hazard_priority(hazard_type: str) -> str:
    """
    Maps hazard type to operational priority level.

    Args:
        hazard_type: Name of detected hazard.

    Returns:
        str: 'critical', 'high', or 'medium'.
    """
    clean_type = hazard_type.strip().lower()
    return PRIORITY_MAP.get(clean_type, "medium")


class IncidentIdGenerator:
    """
    Safely generates unique, sequential Incident IDs (e.g. INC-0001, INC-0002)
    that persist across application restarts by reconciling against existing files on disk.
    """

    ID_PATTERN = re.compile(r"^INC-(\d+)\.(json|jpg|jpeg|png)$", re.IGNORECASE)

    def __init__(self, evidence_dir: Path, test_data_dir: Path) -> None:
        self.evidence_dir = evidence_dir
        self.test_data_dir = test_data_dir
        self._lock = threading.Lock()
        self._current_id = self._find_highest_existing_id()

    def _find_highest_existing_id(self) -> int:
        """Scans evidence and test data directories for existing incident numbers."""
        max_id = 0

        for directory in [self.evidence_dir, self.test_data_dir]:
            if not directory.exists():
                continue
            for file_path in directory.iterdir():
                if file_path.is_file():
                    match = self.ID_PATTERN.match(file_path.name)
                    if match:
                        try:
                            idx = int(match.group(1))
                            if idx > max_id:
                                max_id = idx
                        except ValueError:
                            continue

        logger.info(f"[INCIDENT] Initialized Incident ID generator starting after index {max_id}")
        return max_id

    def next_id(self) -> str:
        """
        Allocates the next unique incident ID in a thread-safe manner.

        Returns:
            str: Formatted incident ID, e.g. 'INC-0001'.
        """
        with self._lock:
            self._current_id += 1
            return f"INC-{self._current_id:04d}"


class EvidencePackager:
    """
    Packages detected road hazards into annotated evidence images and Incident JSON files.
    """

    def __init__(self, cfg: EdgeConfig | None = None) -> None:
        self.cfg = cfg or default_config
        self.cfg.ensure_directories()
        self.id_gen = IncidentIdGenerator(
            evidence_dir=self.cfg.EVIDENCE_DIR,
            test_data_dir=self.cfg.TEST_DATA_DIR,
        )

    def draw_annotation(
        self,
        frame: np.ndarray,
        hazard_type: str,
        confidence: float,
        bbox: list[int] | None = None,
    ) -> np.ndarray:
        """
        Draws bounding box and identification label onto an image frame.
        Supports both [x, y, w, h] and [x1, y1, x2, y2] formats safely.

        Args:
            frame: BGR numpy image array.
            hazard_type: Detected class name.
            confidence: Confidence score (0.0 to 1.0).
            bbox: Optional bounding box coordinate list of 4 ints.

        Returns:
            np.ndarray: Annotated image copy.
        """
        annotated = frame.copy()
        if not bbox or len(bbox) != 4:
            return annotated

        h, w = annotated.shape[:2]
        c1, c2, c3, c4 = bbox

        # Differentiate between [x, y, w, h] and [x1, y1, x2, y2]
        # If c3 and c4 are smaller than w and h and c3 <= c1 or c4 <= c2, it's likely [x, y, w, h]
        if c3 < c1 or c4 < c2:
            x1, y1 = max(0, c1), max(0, c2)
            x2, y2 = min(w - 1, c1 + c3), min(h - 1, c2 + c4)
        else:
            # Assume [x1, y1, x2, y2]
            x1, y1 = max(0, c1), max(0, c2)
            x2, y2 = min(w - 1, c3), min(h - 1, c4)

        # Draw bounding box (vibrant red/amber)
        color = (0, 69, 255)  # Orange-Red in BGR
        thickness = 2
        cv2.rectangle(annotated, (int(x1), int(y1)), (int(x2), int(y2)), color, thickness)

        # Draw label background tag
        label = f"{hazard_type.upper()} ({confidence * 100:.0f}%)"
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.5
        font_thickness = 1
        (text_w, text_h), baseline = cv2.getTextSize(label, font, font_scale, font_thickness)

        tag_y1 = max(0, int(y1) - text_h - 6)
        tag_y2 = int(y1)
        tag_x2 = min(w - 1, int(x1) + text_w + 6)
        cv2.rectangle(annotated, (int(x1), tag_y1), (tag_x2, tag_y2), color, -1)

        # Draw label text
        cv2.putText(
            annotated,
            label,
            (int(x1) + 3, tag_y2 - baseline + 1),
            font,
            font_scale,
            (255, 255, 255),
            font_thickness,
            cv2.LINE_AA,
        )

        return annotated

    def package_incident(
        self,
        frame: np.ndarray,
        detection: dict[str, Any],
        location: dict[str, float],
        timestamp: str,
    ) -> dict[str, Any]:
        """
        Creates and stores the Incident JSON and annotated evidence image.

        Args:
            frame: Video frame where hazard was identified.
            detection: Dict with 'class', 'confidence', and optional 'bbox'.
            location: Dict with 'latitude' and 'longitude'.
            timestamp: UTC ISO-8601 string with 'Z' suffix.

        Returns:
            dict[str, Any]: The finalized incident payload conforming to contract schema.
        """
        incident_id = self.id_gen.next_id()
        hazard_type = str(detection.get("class", "unknown")).strip().lower()
        confidence = float(detection.get("confidence", 0.0))
        bbox = detection.get("bbox")

        # Range validation
        confidence = max(0.0, min(1.0, confidence))
        lat = float(location["latitude"])
        lon = float(location["longitude"])
        if not (-90.0 <= lat <= 90.0) or not (-180.0 <= lon <= 180.0):
            raise ValueError(f"Invalid GPS coordinates for incident: {location}")

        # Construct image relative path with forward slashes
        image_filename = f"{incident_id}.jpg"
        image_file_path = self.cfg.EVIDENCE_DIR / image_filename
        image_url = f"data/evidence/{image_filename}"

        # 1. Annotate and save evidence frame
        annotated_frame = self.draw_annotation(
            frame=frame,
            hazard_type=hazard_type,
            confidence=confidence,
            bbox=bbox,
        )

        success = cv2.imwrite(str(image_file_path), annotated_frame)
        if not success:
            logger.error(f"[EVIDENCE] Failed to write evidence image to {image_file_path}")
        else:
            logger.info(f"[EVIDENCE] saved: {image_file_path.resolve()}")

        # 2. Build standard Incident JSON (Contract with Lohith & Parvati)
        incident_payload: dict[str, Any] = {
            "incident_id": incident_id,
            "type": hazard_type,
            "confidence": round(confidence, 4),
            "latitude": round(lat, 6),
            "longitude": round(lon, 6),
            "timestamp": timestamp,
            "image_url": image_url,
            "source": "bus",
            "bus_id": self.cfg.BUS_ID,
            "status": "pending",
            "priority": get_hazard_priority(hazard_type),
        }

        # 3. Save local JSON file for debugging and offline audit
        json_file_path = self.cfg.TEST_DATA_DIR / f"{incident_id}.json"
        with open(json_file_path, "w", encoding="utf-8") as f:
            json.dump(incident_payload, f, indent=2)

        logger.info(f"[INCIDENT] {incident_id} created (type={hazard_type}, priority={incident_payload['priority']})")
        return incident_payload
