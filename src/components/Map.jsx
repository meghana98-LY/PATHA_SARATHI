import { useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { ArrowRight } from 'lucide-react';

// Bengaluru default coordinates
const BENGALURU_CENTER = [12.9716, 77.5946];
const DEFAULT_ZOOM = 12;

// Custom Marker Icon Creator
const createMarkerIcon = (priority, status, isSelected) => {
  let color = '#ef4444'; // Red (High priority)
  if (priority === 'medium') color = '#f59e0b'; // Amber (Medium)
  if (priority === 'low') color = '#3b82f6'; // Blue (Low)
  if (status === 'resolved') color = '#10b981'; // Green (Resolved)

  const size = isSelected ? 34 : 26;
  const stroke = isSelected ? '#ffffff' : '#0f172a';
  const borderWidth = isSelected ? 3 : 2;

  return L.divIcon({
    className: `gis-marker-container ${isSelected ? 'marker-selected' : ''}`,
    html: `
      <div style="
        background: ${color};
        width: ${size}px;
        height: ${size}px;
        border-radius: 50% 50% 50% 0;
        transform: rotate(-45deg);
        border: ${borderWidth}px solid ${stroke};
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.4), 0 0 ${isSelected ? '12px' : '0px'} ${color};
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
      ">
        <div style="
          width: 8px;
          height: 8px;
          background: #ffffff;
          border-radius: 50%;
          transform: rotate(45deg);
        "></div>
      </div>
    `,
    iconSize: [size, size],
    iconAnchor: [size / 2, size],
    popupAnchor: [0, -size]
  });
};

// Component to handle pan/zoom actions dynamically when selected incident changes
function MapController({ selectedIncident }) {
  const map = useMap();

  useEffect(() => {
    if (selectedIncident && selectedIncident.latitude && selectedIncident.longitude) {
      map.flyTo([selectedIncident.latitude, selectedIncident.longitude], 15, {
        duration: 1.2,
        easeLinearity: 0.25
      });
    }
  }, [selectedIncident, map]);

  return null;
}

export default function Map({ incidents = [], selectedIncident, onSelectIncident, onViewDetails }) {
  const safeIncidents = Array.isArray(incidents) ? incidents.filter(i => i.latitude && i.longitude) : [];

  const formatType = (str) => {
    if (!str) return 'Hazard';
    return str.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
  };

  return (
    <div className="map-wrapper" aria-label="GIS Hazard Map View">
      <MapContainer
        center={BENGALURU_CENTER}
        zoom={DEFAULT_ZOOM}
        scrollWheelZoom={true}
        className="leaflet-map-container"
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        <MapController selectedIncident={selectedIncident} />

        {safeIncidents.map((incident) => {
          const isSelected = selectedIncident?.incident_id === incident.incident_id;
          const icon = createMarkerIcon(incident.priority, incident.status, isSelected);

          return (
            <Marker
              key={incident.incident_id}
              position={[incident.latitude, incident.longitude]}
              icon={icon}
              eventHandlers={{
                click: () => onSelectIncident(incident)
              }}
            >
              <Popup className="incident-leaflet-popup">
                <div className="popup-content">
                  <div className="popup-header">
                    <span className="popup-id">{incident.incident_id}</span>
                    <span className={`priority-badge priority-${incident.priority}`}>
                      {incident.priority ? incident.priority.toUpperCase() : 'NORMAL'}
                    </span>
                  </div>

                  <h4 className="popup-title">{formatType(incident.type)}</h4>

                  <div className="popup-meta">
                    <span className="popup-confidence">
                      Confidence: <strong>{Math.round((incident.confidence || 0) * 100)}%</strong>
                    </span>
                    <span className="popup-source">
                      Source: {incident.source === 'bus' ? `Bus (${incident.bus_id || 'Transit'})` : 'Citizen'}
                    </span>
                  </div>

                  <div className="popup-status-line">
                    Status: <span className={`status-badge status-${incident.status}`}>{incident.status}</span>
                  </div>

                  <button
                    type="button"
                    className="popup-details-btn"
                    onClick={() => onViewDetails(incident)}
                  >
                    View Full Details <ArrowRight size={12} />
                  </button>
                </div>
              </Popup>
            </Marker>
          );
        })}
      </MapContainer>

      {/* Map Legend */}
      <div className="map-legend">
        <div className="legend-title">Priority Legend</div>
        <div className="legend-items">
          <div className="legend-item"><span className="legend-dot red"></span> High</div>
          <div className="legend-item"><span className="legend-dot amber"></span> Medium</div>
          <div className="legend-item"><span className="legend-dot blue"></span> Low</div>
          <div className="legend-item"><span className="legend-dot green"></span> Resolved</div>
        </div>
      </div>
    </div>
  );
}
