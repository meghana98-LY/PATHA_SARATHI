"""
Camera and video capture module for the PATHA SARATHI Edge Capture Module.
Handles frame acquisition from webcams, video files, or mock sources.
Does NOT contain any AI or detection logic.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import cv2
import numpy as np

logger = logging.getLogger(__name__)


class CameraCapture:
    """
    Acquires video frames from a webcam index or video file path.
    Guarantees consistent frame numbering and UTC ISO-8601 timestamps.
    """

    def __init__(self, source: int | str | Path = 0) -> None:
        """
        Initializes camera capture source.

        Args:
            source: Webcam device index (int) or path to a video file.
                    Can also be string 'mock' for synthetic frame generation.
        """
        self.source = source
        self._cap: cv2.VideoCapture | None = None
        self._frame_number: int = 0
        self._is_started: bool = False
        self._is_mock: bool = str(source).strip().lower() == "mock"

    @property
    def frame_number(self) -> int:
        """Current frame counter."""
        return self._frame_number

    @property
    def is_opened(self) -> bool:
        """Checks if the video capture source is actively accessible."""
        if self._is_mock:
            return self._is_started
        return bool(self._cap is not None and self._cap.isOpened())

    def start(self) -> bool:
        """
        Opens the camera device or video file stream.
        Handles invalid or unreachable sources gracefully without crashing.

        Returns:
            bool: True if source opened successfully, False otherwise.
        """
        self._frame_number = 0

        if self._is_mock:
            self._is_started = True
            logger.info("[EDGE] Mock camera started (synthetic frames)")
            return True

        # Handle numeric string as webcam index if passed as string "0"
        resolved_source: int | str
        if isinstance(self.source, int):
            resolved_source = self.source
        elif isinstance(self.source, Path):
            resolved_source = str(self.source)
        elif isinstance(self.source, str) and self.source.isdigit():
            resolved_source = int(self.source)
        else:
            resolved_source = str(self.source)

        # If it's a file path, log informative message if file doesn't exist
        if isinstance(resolved_source, str) and not resolved_source.isdigit():
            if not Path(resolved_source).exists():
                logger.warning(
                    f"[EDGE] Video source file not found: {resolved_source}. "
                    "VideoCapture may fail to open."
                )

        try:
            self._cap = cv2.VideoCapture(resolved_source)
            if not self._cap.isOpened():
                logger.error(f"[EDGE] Failed to open video source: {self.source}")
                self._is_started = False
                return False

            self._is_started = True
            logger.info(f"[EDGE] Camera started successfully (source={self.source})")
            return True
        except Exception as e:
            logger.error(f"[EDGE] Unexpected error opening camera source '{self.source}': {e}")
            self._is_started = False
            return False

    def read_frame(self) -> dict[str, Any] | None:
        """
        Reads the next video frame.

        Returns:
            dict containing:
                - 'frame' (np.ndarray): The captured BGR image.
                - 'frame_number' (int): Sequential 1-based frame index.
                - 'timestamp' (str): UTC ISO-8601 timestamp with 'Z' suffix.
            or None if the stream ended or frame could not be retrieved.
        """
        if not self._is_started:
            logger.warning("[EDGE] Attempted to read_frame before start() or after release().")
            return None

        # Synthetic mock frame support
        if self._is_mock:
            self._frame_number += 1
            # Generate a 640x480 synthetic road-like frame
            synthetic_frame = np.zeros((480, 640, 3), dtype=np.uint8)
            # Add synthetic gray road surface
            synthetic_frame[200:, :] = (50, 50, 50)
            # Add timestamp in UTC ISO-8601 format with 'Z' suffix
            now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            return {
                "frame": synthetic_frame,
                "frame_number": self._frame_number,
                "timestamp": now_utc,
            }

        if self._cap is None or not self._cap.isOpened():
            return None

        try:
            ret, frame = self._cap.read()
            if not ret or frame is None:
                logger.debug(f"[EDGE] End of stream or empty frame reached at frame {self._frame_number}.")
                return None

            self._frame_number += 1
            now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

            return {
                "frame": frame,
                "frame_number": self._frame_number,
                "timestamp": now_utc,
            }
        except Exception as e:
            logger.error(f"[EDGE] Error reading frame {self._frame_number + 1}: {e}")
            return None

    def release(self) -> None:
        """Releases the camera device or video file stream."""
        if self._cap is not None:
            try:
                self._cap.release()
            except Exception as e:
                logger.warning(f"[EDGE] Error releasing VideoCapture: {e}")
            self._cap = None

        self._is_started = False
        logger.info("[EDGE] Camera released")

    def __enter__(self) -> CameraCapture:
        self.start()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.release()
