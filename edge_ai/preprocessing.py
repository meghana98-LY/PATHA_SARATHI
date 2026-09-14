"""
Image and video frame preprocessing utilities for PATHA SARATHI Edge AI.
"""

from __future__ import annotations

import cv2
import numpy as np


def resize_frame(frame: np.ndarray, width: int = 640, height: int = 480) -> np.ndarray:
    """
    Resize input frame to target dimensions.

    Args:
        frame: Input image array (BGR).
        width: Desired target width in pixels.
        height: Desired target height in pixels.

    Returns:
        Resized numpy image array.
    """
    return cv2.resize(frame, (width, height), interpolation=cv2.INTER_AREA)


def normalize_frame(frame: np.ndarray) -> np.ndarray:
    """
    Normalize pixel values to [0, 1] float range.

    Args:
        frame: Input image array (BGR or RGB).

    Returns:
        Normalized float32 array.
    """
    return frame.astype(np.float32) / 255.0

