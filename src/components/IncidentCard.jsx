import { Bus, User, MapPin, Percent, Calendar } from 'lucide-react';

export default function IncidentCard({ incident, isSelected, onSelect }) {
  const {
    incident_id,
    type,
    confidence,
    latitude,
    longitude,
    timestamp,
    source,
    bus_id,
    status,
    priority,
    location_name
  } = incident;

  // Format type string for display (e.g., road_damage -> Road Damage)
  const formatType = (str) => {
    if (!str) return 'Hazard';
    return str
      .split('_')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  };

  // Format timestamp into human-readable date & time
  const formatDate = (isoString) => {
    if (!isoString) return 'N/A';
    try {
      const date = new Date(isoString);
      return date.toLocaleString('en-IN', {
        day: '2-digit',
        month: 'short',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch {
      return isoString;
    }
  };

  // Convert decimal confidence (0.91) to percentage (91%)
  const confidencePct = Math.round((confidence || 0) * 100);

  return (
    <div
      className={`incident-card ${isSelected ? 'selected' : ''} priority-${priority}`}
      onClick={() => onSelect(incident)}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          onSelect(incident);
        }
      }}
      aria-label={`Incident ${incident_id}: ${formatType(type)}`}
    >
      <div className="incident-card-header">
        <div className="incident-id-badge">
          <span className="id-text">{incident_id}</span>
          <span className={`priority-badge priority-${priority}`}>
            {priority ? priority.toUpperCase() : 'NORMAL'}
          </span>
        </div>
        <span className={`status-badge status-${status}`}>
          {status ? status.replace('_', ' ') : 'pending'}
        </span>
      </div>

      <div className="incident-card-title">
        <h3>{formatType(type)}</h3>
        {location_name && <p className="location-name"><MapPin size={13} /> {location_name}</p>}
      </div>

      <div className="incident-card-metrics">
        <div className="metric-chip confidence" title="AI Detection Confidence">
          <Percent size={13} />
          <span>{confidencePct}% Confidence</span>
        </div>

        <div className="metric-chip source" title={`Reported via ${source}`}>
          {source === 'bus' ? (
            <>
              <Bus size={13} />
              <span>{bus_id || 'Bus Transit'}</span>
            </>
          ) : (
            <>
              <User size={13} />
              <span>Citizen Report</span>
            </>
          )}
        </div>
      </div>

      <div className="incident-card-footer">
        <div className="coordinates" title="Coordinates">
          <MapPin size={12} />
          <span>{latitude?.toFixed(4)}, {longitude?.toFixed(4)}</span>
        </div>
        <div className="timestamp">
          <Calendar size={12} />
          <span>{formatDate(timestamp)}</span>
        </div>
      </div>
    </div>
  );
}
