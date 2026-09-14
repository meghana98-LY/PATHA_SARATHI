// PATHA SARATHI - GIS Dashboard API Service

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000/api';

// Initial fallback/mock incident data for demonstration and offline mode
export const MOCK_INCIDENTS = [
  {
    incident_id: "INC001",
    raw_id: 1,
    type: "pothole",
    confidence: 0.91,
    latitude: 12.9716,
    longitude: 77.5946,
    timestamp: "2026-09-12T10:30:20",
    image_url: "",
    source: "bus",
    bus_id: "BUS_101",
    status: "pending",
    priority: "high",
    priority_score: 85,
    location_name: "MG Road, Central Bengaluru"
  },
  {
    incident_id: "INC002",
    raw_id: 2,
    type: "road_damage",
    confidence: 0.87,
    latitude: 12.9352,
    longitude: 77.6245,
    timestamp: "2026-09-12T11:10:00",
    image_url: "",
    source: "citizen",
    bus_id: null,
    status: "verified",
    priority: "medium",
    priority_score: 55,
    location_name: "Koramangala 5th Block"
  },
  {
    incident_id: "INC003",
    raw_id: 3,
    type: "road_obstruction",
    confidence: 0.94,
    latitude: 12.9850,
    longitude: 77.6100,
    timestamp: "2026-09-12T12:00:00",
    image_url: "",
    source: "bus",
    bus_id: "BUS_102",
    status: "resolved",
    priority: "low",
    priority_score: 25,
    location_name: "Indiranagar 100ft Road"
  },
  {
    incident_id: "INC004",
    raw_id: 4,
    type: "pothole",
    confidence: 0.95,
    latitude: 12.9279,
    longitude: 77.6811,
    timestamp: "2026-09-13T08:15:30",
    image_url: "",
    source: "bus",
    bus_id: "BUS_204",
    status: "pending",
    priority: "high",
    priority_score: 90,
    location_name: "Outer Ring Road, Bellandur"
  },
  {
    incident_id: "INC005",
    raw_id: 5,
    type: "road_damage",
    confidence: 0.89,
    latitude: 12.9900,
    longitude: 77.5500,
    timestamp: "2026-09-13T09:40:12",
    image_url: "",
    source: "citizen",
    bus_id: null,
    status: "pending",
    priority: "medium",
    priority_score: 60,
    location_name: "Rajajinagar Metro Station"
  },
  {
    incident_id: "INC006",
    raw_id: 6,
    type: "pothole",
    confidence: 0.98,
    latitude: 12.9698,
    longitude: 77.7500,
    timestamp: "2026-09-13T11:05:45",
    image_url: "",
    source: "bus",
    bus_id: "BUS_305",
    status: "pending",
    priority: "high",
    priority_score: 95,
    location_name: "ITPL Main Road, Whitefield"
  }
];

/**
 * Normalizes backend hazard types into standard lowercase snake_case.
 */
function normalizeHazardType(hazardType) {
  if (!hazardType) return "pothole";

  return hazardType
    .toString()
    .trim()
    .toLowerCase()
    .replace(/[\s-]+/g, "_");
}

/**
 * Maps numerical priority scores to frontend priority labels.
 */
function getPriorityLabel(priorityScore) {
  const score = Number(priorityScore) || 0;

  if (score >= 70) return "high";
  if (score >= 40) return "medium";

  return "low";
}

/**
 * Normalizes backend status values into frontend status labels.
 */
function normalizeStatus(status) {
  if (!status) return "pending";

  const s = status.toString().trim().toUpperCase();

  if (s === "RESOLVED") return "resolved";
  if (s === "IN_PROGRESS") return "in_progress";
  if (s === "VERIFIED") return "verified";
  if (s === "REPORTED" || s === "PENDING") return "pending";

  return s.toLowerCase();
}

/**
 * Transforms a raw backend incident record into
 * the standard frontend representation.
 */
function transformBackendIncident(item) {
  if (!item || typeof item !== "object") return null;

  const rawId =
    item.id !== undefined
      ? item.id
      : item.raw_id !== undefined
        ? item.raw_id
        : null;

  const incidentCode =
    item.incident_code ||
    item.incident_id ||
    (rawId !== null ? `INC${rawId}` : `INC_${Date.now()}`);

  const score =
    item.priority_score !== undefined
      ? Number(item.priority_score)
      : 50;

  const lat = Number(item.latitude) || 0;
  const lng = Number(item.longitude) || 0;

  return {
    raw_id: rawId,
    incident_id: incidentCode,
    type: normalizeHazardType(item.hazard_type || item.type),
    confidence:
      item.confidence !== undefined
        ? Number(item.confidence)
        : 0.85,
    latitude: lat,
    longitude: lng,
    timestamp:
      item.first_reported_at ||
      item.last_updated_at ||
      item.timestamp ||
      new Date().toISOString(),
    image_url: item.image_url || "",
    source:
      item.source ||
      (item.device_id ? "bus" : "citizen"),
    bus_id:
      item.device_id ||
      item.bus_id ||
      (item.source === "bus" ? "BUS_NODE_01" : null),
    status: normalizeStatus(item.status),
    priority: getPriorityLabel(score),
    priority_score: score,
    location_name:
      item.location_name ||
      `Lat: ${lat.toFixed(4)}, Lng: ${lng.toFixed(4)}`
  };
}

/**
 * Fetches road hazard incidents from backend API.
 */
export async function fetchIncidents() {
  try {
    const response = await fetch(
      `${API_BASE_URL}/incidents`,
      {
        method: "GET",
        headers: {
          Accept: "application/json",
        },
      }
    );

    if (!response.ok) {
      throw new Error(
        `Server returned HTTP ${response.status}`
      );
    }

    const data = await response.json();

    let rawList = [];

    if (Array.isArray(data)) {
      rawList = data;
    } else if (
      data &&
      Array.isArray(data.incidents)
    ) {
      rawList = data.incidents;
    } else {
      throw new Error(
        "Invalid incident data structure returned from API"
      );
    }

    const transformedList = rawList
      .map(transformBackendIncident)
      .filter(item => item !== null);

    return transformedList.length > 0
      ? transformedList
      : MOCK_INCIDENTS;
  } catch (error) {
    console.warn(
      "Backend API unavailable, using sample incident data:",
      error.message
    );

    return MOCK_INCIDENTS;
  }
}

/**
 * Update an incident's status via PATCH request.
 */
export async function updateIncidentStatus(
  incidentId,
  newStatus
) {
  try {
    let targetId = incidentId;

    if (
      typeof incidentId === "object" &&
      incidentId !== null
    ) {
      targetId =
        incidentId.raw_id !== undefined &&
        incidentId.raw_id !== null
          ? incidentId.raw_id
          : incidentId.incident_id;
    }

    const response = await fetch(
      `${API_BASE_URL}/incidents/${targetId}/status`,
      {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          status: newStatus,
        }),
      }
    );

    if (!response.ok) {
      throw new Error(
        `Failed to update status on server (HTTP ${response.status})`
      );
    }

    return await response.json();
  } catch (err) {
    console.warn(
      `Local status change for ${
        typeof incidentId === "object"
          ? incidentId.incident_id
          : incidentId
      } to ${newStatus} (offline mode):`,
      err.message
    );

    return {
      success: true,
      incident_id: incidentId,
      status: newStatus,
    };
  }
}

/**
 * Fetches persistent authority alerts generated
 * by Medha's Authority Action service.
 */
export async function fetchAuthorityAlerts() {
  const response = await fetch(
    `${API_BASE_URL}/alerts`,
    {
      method: "GET",
      headers: {
        Accept: "application/json",
      },
    }
  );

  if (!response.ok) {
    throw new Error(
      `Failed to fetch authority alerts (HTTP ${response.status})`
    );
  }

  const data = await response.json();

  if (!data || !Array.isArray(data.alerts)) {
    throw new Error(
      "Invalid authority alert data structure returned from API"
    );
  }

  return data.alerts;
}

/**
 * Updates the status of an authority alert.
 */
export async function updateAuthorityAlertStatus(
  alertId,
  newStatus
) {
  const response = await fetch(
    `${API_BASE_URL}/alerts/${alertId}/status`,
    {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        status: newStatus,
      }),
    }
  );

  if (!response.ok) {
    throw new Error(
      `Failed to update authority alert status (HTTP ${response.status})`
    );
  }

  return await response.json();
}