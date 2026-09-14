import { useState } from 'react';
import {
  BellRing,
  Building2,
  MapPin,
  Users,
  CheckCircle2,
  Clock3,
  AlertTriangle,
  Loader2
} from 'lucide-react';

import { updateAuthorityAlertStatus } from '../services/api';

function formatStatus(status) {
  return status
    .toLowerCase()
    .replace(/_/g, ' ')
    .replace(/\b\w/g, char => char.toUpperCase());
}

function formatPriority(priority) {
  return priority?.toUpperCase() || 'UNKNOWN';
}

export default function AuthorityAlerts({
  alerts,
  loading,
  onAlertUpdated
}) {
  const [updatingAlertId, setUpdatingAlertId] = useState(null);

  const handleStatusChange = async (alertId, newStatus) => {
    try {
      setUpdatingAlertId(alertId);

      const result = await updateAuthorityAlertStatus(
        alertId,
        newStatus
      );

      if (result?.alert) {
        onAlertUpdated?.(result.alert);
      }
    } catch (error) {
      console.error(
        'Authority alert status update failed:',
        error
      );
    } finally {
      setUpdatingAlertId(null);
    }
  };

  const getPriorityClass = priority => {
    const value = priority?.toLowerCase();

    if (value === 'critical') return 'priority-critical';
    if (value === 'high') return 'priority-high';
    if (value === 'medium') return 'priority-medium';

    return 'priority-low';
  };

  const getStatusClass = status => {
    const value = status?.toLowerCase();

    if (value === 'pending_action') {
      return 'alert-status-pending';
    }

    if (value === 'in_progress') {
      return 'alert-status-progress';
    }

    if (value === 'resolved') {
      return 'alert-status-resolved';
    }

    return 'alert-status-rejected';
  };

  if (loading) {
    return (
      <section className="authority-alerts-panel">
        <div className="authority-alerts-header">
          <div className="authority-alerts-title">
            <BellRing size={18} />
            <div>
              <h2>Authority Alerts</h2>
              <span>Action required incidents</span>
            </div>
          </div>
        </div>

        <div className="authority-alerts-loading">
          <Loader2 size={24} className="spin" />
          <span>Loading authority alerts...</span>
        </div>
      </section>
    );
  }

  return (
    <section className="authority-alerts-panel">
      <div className="authority-alerts-header">
        <div className="authority-alerts-title">
          <div className="authority-alerts-icon">
            <BellRing size={18} />
          </div>

          <div>
            <h2>Authority Alerts</h2>
            <span>
              {alerts.length} alert{alerts.length !== 1 ? 's' : ''}
            </span>
          </div>
        </div>

        <div className="authority-alerts-live">
          <span className="authority-alerts-live-dot" />
          LIVE
        </div>
      </div>

      {alerts.length === 0 ? (
        <div className="authority-alerts-empty">
          <CheckCircle2 size={32} />
          <strong>No active authority alerts</strong>
          <span>
            Verified incidents requiring authority action will
            appear here.
          </span>
        </div>
      ) : (
        <div className="authority-alerts-list">
          {alerts.map(alert => (
            <article
              key={alert.alert_id}
              className={`authority-alert-card ${getPriorityClass(
                alert.priority
              )}`}
            >
              <div className="authority-alert-card-header">
                <div>
                  <span className="authority-alert-id">
                    {alert.alert_id}
                  </span>

                  <h3>
                    {alert.hazard_type}
                  </h3>
                </div>

                <span
                  className={`authority-priority-badge ${getPriorityClass(
                    alert.priority
                  )}`}
                >
                  <AlertTriangle size={12} />
                  {formatPriority(alert.priority)}
                </span>
              </div>

              <div className="authority-alert-details">
                <div className="authority-alert-detail">
                  <MapPin size={14} />
                  <span>
                    {alert.latitude}, {alert.longitude}
                  </span>
                </div>

                <div className="authority-alert-detail">
                  <Building2 size={14} />
                  <span>
                    {alert.department || 'Unassigned Department'}
                  </span>
                </div>

                <div className="authority-alert-detail">
                  <Users size={14} />
                  <span>
                    {alert.assigned_team || 'Unassigned Team'}
                  </span>
                </div>

                <div className="authority-alert-detail">
                  <Clock3 size={14} />
                  <span>
                    Confidence:{' '}
                    {(Number(alert.confidence) * 100).toFixed(0)}%
                  </span>
                </div>
              </div>

              <div className="authority-alert-footer">
                <span
                  className={`authority-status-badge ${getStatusClass(
                    alert.status
                  )}`}
                >
                  {formatStatus(alert.status)}
                </span>

                <select
                  className="authority-status-select"
                  value={alert.status}
                  disabled={
                    updatingAlertId === alert.alert_id
                  }
                  onChange={event =>
                    handleStatusChange(
                      alert.alert_id,
                      event.target.value
                    )
                  }
                >
                  <option value="PENDING_ACTION">
                    Pending Action
                  </option>

                  <option value="IN_PROGRESS">
                    In Progress
                  </option>

                  <option value="RESOLVED">
                    Resolved
                  </option>

                  <option value="REJECTED">
                    Rejected
                  </option>
                </select>
              </div>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}