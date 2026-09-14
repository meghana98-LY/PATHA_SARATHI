"""
Detector integration layer for PATHA SARATHI Edge AI.

Provides the detector interface used by the edge pipeline and adapts
Kishor's RoadHazardDetector to the detector interface.
"""

from __future__ import annotations

from typing import Any

from edge_ai.detector_kishor import RoadHazardDetector


class KishorDetector:
    """
    Adapter around Kishor's RoadHazardDetector.

    Converts Kishor's detector output into the interface expected
    by EdgePipeline.
    """

    def __init__(
        self,
        repo_id: str = "rezzzq/yolo12s-road-damage-rdd2022",
        filename: str = "model.pt",
    ) -> None:
        self.detector = RoadHazardDetector(
            repo_id=repo_id,
            filename=filename,
        )

    def detect(self, frame: Any) -> list[dict[str, Any]]:
        """Run Kishor's YOLO detector on a video frame."""
        return self.detector.detect(frame)


__all__ = [
    "KishorDetector",
]