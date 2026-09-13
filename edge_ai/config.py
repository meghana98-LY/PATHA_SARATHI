"""
Configuration management for the PATHA SARATHI Edge Capture Module.
Loads settings from environment variables with sensible defaults using pathlib.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from dotenv import load_dotenv

# Project Root Directory: D:\SIH (parent of edge_ai/)
BASE_DIR: Path = Path(__file__).resolve().parent.parent

# Load .env file from project root if present
load_dotenv(dotenv_path=BASE_DIR / ".env")


def _get_video_source(val: str | None) -> int | str:
    """Parses video source string into an int index (if digits) or file path string."""
    if not val:
        return 0
    val_clean = val.strip()
    if val_clean.isdigit():
        return int(val_clean)
    return val_clean


@dataclass(frozen=True)
class EdgeConfig:
    """Immutable configuration container for edge capture pipeline."""

    # Bus Identity
    BUS_ID: str = field(
        default_factory=lambda: os.getenv("BUS_ID", "BUS_101").strip()
    )

    # Video Source (webcam index int or video file path)
    VIDEO_SOURCE: int | str = field(
        default_factory=lambda: _get_video_source(os.getenv("VIDEO_SOURCE", "0"))
    )

    # AI Detection Controls
    FRAME_SKIP: int = field(
        default_factory=lambda: max(1, int(os.getenv("FRAME_SKIP", "5")))
    )
    CONFIDENCE_THRESHOLD: float = field(
        default_factory=lambda: max(
            0.0, min(1.0, float(os.getenv("CONFIDENCE_THRESHOLD", "0.5")))
        )
    )
    DETECTION_COOLDOWN_FRAMES: int = field(
        default_factory=lambda: max(0, int(os.getenv("DETECTION_COOLDOWN_FRAMES", "30")))
    )

    # GPS Parameters
    GPS_MODE: str = field(
        default_factory=lambda: os.getenv("GPS_MODE", "simulation").strip().lower()
    )
    GPS_EXHAUSTION_BEHAVIOR: str = field(
        default_factory=lambda: os.getenv("GPS_EXHAUSTION_BEHAVIOR", "loop").strip().lower()
    )

    # Backend Integration
    BACKEND_URL: str = field(
        default_factory=lambda: os.getenv("BACKEND_URL", "http://localhost:8000").rstrip("/")
    )

    # Storage Paths
    OUTPUT_DIR: Path = field(
        default_factory=lambda: BASE_DIR / os.getenv("OUTPUT_DIR", "data")
    )

    @property
    def EVIDENCE_DIR(self) -> Path:
        """Directory where annotated evidence frames (.jpg) are stored."""
        return self.OUTPUT_DIR / "evidence"

    @property
    def TEST_DATA_DIR(self) -> Path:
        """Directory where local incident payloads (.json) are stored."""
        return self.OUTPUT_DIR / "test_data"

    @property
    def SAMPLE_VIDEOS_DIR(self) -> Path:
        """Directory containing sample test videos."""
        return self.OUTPUT_DIR / "sample_videos"

    @property
    def SAMPLE_IMAGES_DIR(self) -> Path:
        """Directory containing sample test images."""
        return self.OUTPUT_DIR / "sample_images"

    def ensure_directories(self) -> None:
        """Creates storage directories if they do not exist."""
        self.EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
        self.TEST_DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.SAMPLE_VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
        self.SAMPLE_IMAGES_DIR.mkdir(parents=True, exist_ok=True)


# Default global instance
config = EdgeConfig()
