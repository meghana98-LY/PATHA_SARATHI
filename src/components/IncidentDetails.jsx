import { X, MapPin, Bus, User, Calendar, ExternalLink, Image as ImageIcon } from 'lucide-react';

export default function IncidentDetails({ incident, onClose, onStatusChange, onFocusMap }) {
  if (!incident) return null;

  const {
    incident_id,
    type,
    confidence,
    latitude,
    longitude,
    timestamp,
    image_url,
    source,
    bus_id,
    status,
    priority,
    location_name
  } = incident;

  const formatType = (str) => {
    if (!str) return 'Road Hazard';
    return str
      .split('_')
      .map(w => w.charAt(0).toUpperCase() + w.slice(1))
      .join(' ');
  };

  const formatDate = (isoString) => {
    if (!isoString) return 'N/A';
    try {
      const date = new Date(isoString);
      return date.toLocaleString('en-IN', {
        dateStyle: 'medium',
        timeStyle: 'medium'
      });
    } catch {
      return isoString;
    }
  };

  const confidencePct = Math.round((confidence || 0) * 100);

  return (
    <div className="incident-details-overlay">
      <div className="incident-details-modal" role="dialog" aria-labelledby="details-title">
        <div className="details-header">
          <div className="details-header-title">
            <span className={`priority-pill priority-${priority}`}>
              {priority ? priority.toUpperCase() : 'NORMAL'} PRIORITY
            </span>
            <h2 id="details-title">{incident_id}: {formatType(type)}</h2>
          </div>
          <button
            type="button"
            className="details-close-btn"
            onClick={onClose}
            aria-label="Close details dialog"
          >
            <X size={20} />
          </button>
        </div>

        <div className="details-body">
          {/* Main Info Card Grid */}
          <div className="details-grid">
            <div className="detail-item">
              <span className="detail-label">Status</span>
              <div className="status-selector-wrapper">
                <span className={`status-badge status-${status}`}>
                  {status ? status.replace('_', ' ') : 'pending'}
                </span>
                {onStatusChange && (
                  <select
                    className="status-dropdown"
                    value={status}
                    onChange={(e) => onStatusChange(incident_id, e.target.value)}
                    aria-label="Update incident status"
                  >
                    <option value="pending">Mark as Pending</option>
                    <option value="verified">Mark as Verified</option>
                    <option value="in_progress">Mark in Progress</option>
                    <option value="resolved">Mark as Resolved</option>
                  </select>
                )}
              </div>
            </div>

            <div className="detail-item">
              <span className="detail-label">AI Confidence Score</span>
              <div className="confidence-meter-container">
                <div className="confidence-meter-bar">
                  <div
                    className="confidence-meter-fill"
                    style={{ width: `${confidencePct}%` }}
                  ></div>
                </div>
                <span className="confidence-value">{confidencePct}%</span>
              </div>
            </div>

            <div className="detail-item">
              <span className="detail-label">Source & Vehicle</span>
              <div className="detail-value flex-align">
                {source === 'bus' ? (
                  <>
                    <Bus size={16} className="text-bus" />
                    <span>Public Bus ({bus_id || 'Transit Fleet'})</span>
                  </>
                ) : (
                  <>
                    <User size={16} className="text-citizen" />
                    <span>Citizen Report</span>
                  </>
                )}
              </div>
            </div>

            <div className="detail-item">
              <span className="detail-label">Report Timestamp</span>
              <div className="detail-value flex-align">
                <Calendar size={16} />
                <span>{formatDate(timestamp)}</span>
              </div>
            </div>

            <div className="detail-item full-width">
              <span className="detail-label">GPS Coordinates</span>
              <div className="detail-value flex-align coords-box">
                <MapPin size={16} className="text-pin" />
                <code>Lat: {latitude}, Lng: {longitude}</code>
                {location_name && <span className="location-tag">({location_name})</span>}
                <button
                  type="button"
                  className="center-map-btn"
                  onClick={() => onFocusMap && onFocusMap(incident)}
                  title="Center map on this incident"
                >
                  <ExternalLink size={14} /> Center Map
                </button>
              </div>
            </div>
          </div>

          {/* Optional Detection Image */}
          {image_url ? (
            <div className="details-image-section">
              <span className="detail-label">Detection Image Snapshot</span>
              <div className="image-frame">
                <img src={image_url} alt={`Hazard snapshot for ${incident_id}`} />
              </div>
            </div>
          ) : (
            <div className="details-no-image">
              <ImageIcon size={24} />
              <span>No image snapshot attached to report</span>
            </div>
          )}
        </div>

        <div className="details-footer">
          <button type="button" className="btn-secondary" onClick={onClose}>
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
