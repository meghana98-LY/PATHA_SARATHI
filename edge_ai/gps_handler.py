"""
GPS acquisition and simulation module for PATHA SARATHI.
Provides coordinates via pluggable adapters (simulation vs. real hardware).
Does NOT depend on camera, detector, or backend layers.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Sequence

logger = logging.getLogger(__name__)

# Sample bus route coordinates in Bangalore, India (used as default simulation track)
DEFAULT_ROUTE: list[dict[str, float]] = [
    {"latitude": 12.9716, "longitude": 77.5946},
    {"latitude": 12.9722, "longitude": 77.5954},
    {"latitude": 12.9730, "longitude": 77.5962},
    {"latitude": 12.9741, "longitude": 77.5975},
    {"latitude": 12.9750, "longitude": 77.5988},
    {"latitude": 12.9763, "longitude": 77.6001},
    {"latitude": 12.9775, "longitude": 77.6015},
    {"latitude": 12.9788, "longitude": 77.6030},
    {"latitude": 12.9801, "longitude": 77.6045},
    {"latitude": 12.9815, "longitude": 77.6060},
]


def _validate_coordinates(lat: float, lon: float) -> tuple[float, float]:
    """
    Validates geographical latitude and longitude bounds.

    Args:
        lat: Latitude in decimal degrees (-90.0 to 90.0).
        lon: Longitude in decimal degrees (-180.0 to 180.0).

    Returns:
        tuple[float, float]: Validated (latitude, longitude).

    Raises:
        ValueError: If coordinates are out of geographical range.
    """
    if not (-90.0 <= lat <= 90.0):
        raise ValueError(f"Latitude out of bounds [-90, 90]: {lat}")
    if not (-180.0 <= lon <= 180.0):
        raise ValueError(f"Longitude out of bounds [-180, 180]: {lon}")
    return float(lat), float(lon)


class BaseGPSAdapter(ABC):
    """Abstract interface for GPS hardware or simulator."""

    @abstractmethod
    def read_coordinates(self) -> dict[str, float]:
        """Returns {'latitude': float, 'longitude': float}."""
        pass


class SimulatedGPSAdapter(BaseGPSAdapter):
    """
    Simulates bus route progression by sequencing through a pre-defined route.
    """

    def __init__(
        self,
        route: Sequence[dict[str, float]] | None = None,
        exhaustion_behavior: str = "loop",
    ) -> None:
        """
        Args:
            route: List of {'latitude': float, 'longitude': float} points.
            exhaustion_behavior: 'loop' to restart the track, or 'hold' to stay at the last point.
        """
        raw_route = route if route else DEFAULT_ROUTE
        self._route: list[dict[str, float]] = []
        for pt in raw_route:
            lat, lon = _validate_coordinates(pt["latitude"], pt["longitude"])
            self._route.append({"latitude": lat, "longitude": lon})

        if not self._route:
            # Fallback default coordinate
            self._route = [{"latitude": 12.9716, "longitude": 77.5946}]

        self._index: int = 0
        self._behavior: str = exhaustion_behavior.strip().lower()

    def read_coordinates(self) -> dict[str, float]:
        """Advances and returns current simulated location."""
        total = len(self._route)
        if self._behavior == "hold":
            idx = min(self._index, total - 1)
        else:  # default is 'loop'
            idx = self._index % total

        point = self._route[idx]
        self._index += 1
        return {"latitude": point["latitude"], "longitude": point["longitude"]}


class RealGPSAdapter(BaseGPSAdapter):
    """
    Placeholder adapter for real NMEA/USB hardware GPS receivers.
    Can be replaced without altering the rest of the edge pipeline.
    """

    def __init__(self, port: str = "/dev/ttyUSB0", baud_rate: int = 9600) -> None:
        self.port = port
        self.baud_rate = baud_rate
        logger.info(f"[GPS] Real GPS adapter configured on port {port} (Baud: {baud_rate})")

    def read_coordinates(self) -> dict[str, float]:
        """Reads from hardware receiver. Falls back to default if hardware is unattached."""
        logger.warning("[GPS] Real hardware adapter not connected; returning fallback coordinate.")
        return {"latitude": 12.9716, "longitude": 77.5946}


class GPSHandler:
    """
    High-level GPS manager for the Edge Capture module.
    Always returns a valid location dict: {'latitude': float, 'longitude': float}.
    """

    def __init__(
        self,
        mode: str = "simulation",
        route: Sequence[dict[str, float]] | None = None,
        exhaustion_behavior: str = "loop",
        adapter: BaseGPSAdapter | None = None,
    ) -> None:
        """
        Initializes GPS handler.

        Args:
            mode: 'simulation' or 'real'.
            route: Optional list of simulated route coordinates.
            exhaustion_behavior: 'loop' or 'hold' when route ends.
            adapter: Optional custom adapter instance.
        """
        self.mode = mode.strip().lower()
        if adapter is not None:
            self._adapter: BaseGPSAdapter = adapter
        elif self.mode == "real":
            self._adapter = RealGPSAdapter()
        else:
            self._adapter = SimulatedGPSAdapter(
                route=route, exhaustion_behavior=exhaustion_behavior
            )

    def get_location(self) -> dict[str, float]:
        """
        Acquires current GPS coordinates. Always guaranteed to return valid floats.

        Returns:
            dict[str, float]: {'latitude': float, 'longitude': float}
        """
        try:
            coords = self._adapter.read_coordinates()
            lat, lon = _validate_coordinates(coords["latitude"], coords["longitude"])
            logger.debug(f"[GPS] latitude={lat} longitude={lon}")
            return {"latitude": lat, "longitude": lon}
        except Exception as e:
            logger.error(f"[GPS] Error reading coordinates from adapter: {e}. Falling back to default.")
            return {"latitude": 12.9716, "longitude": 77.5946}
