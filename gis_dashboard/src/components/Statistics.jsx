import { Layers, AlertTriangle, Clock, CheckCircle2 } from 'lucide-react';

export default function Statistics({ incidents = [], activeFilter, onSelectFilter }) {
  const total = incidents.length;
  const highPriority = incidents.filter(i => i.priority === 'high').length;
  const pending = incidents.filter(i => i.status === 'pending').length;
  const resolved = incidents.filter(i => i.status === 'resolved').length;

  const stats = [
    {
      id: 'total',
      label: 'Total Incidents',
      value: total,
      icon: Layers,
      color: 'stat-blue',
      filterType: 'all',
      description: 'All reported road hazards'
    },
    {
      id: 'high',
      label: 'High Priority',
      value: highPriority,
      icon: AlertTriangle,
      color: 'stat-red',
      filterType: 'high_priority',
      description: 'Requires urgent action'
    },
    {
      id: 'pending',
      label: 'Pending',
      value: pending,
      icon: Clock,
      color: 'stat-amber',
      filterType: 'pending_status',
      description: 'Awaiting inspection'
    },
    {
      id: 'resolved',
      label: 'Resolved',
      value: resolved,
      icon: CheckCircle2,
      color: 'stat-emerald',
      filterType: 'resolved_status',
      description: 'Fixed & verified'
    }
  ];

  return (
    <div className="stats-container" aria-label="Incident Statistics Summary">
      {stats.map((stat) => {
        const IconComponent = stat.icon;
        const isActive = activeFilter === stat.filterType;

        return (
          <div
            key={stat.id}
            className={`stat-card ${stat.color} ${isActive ? 'active' : ''}`}
            onClick={() => onSelectFilter && onSelectFilter(stat.filterType)}
            role="button"
            tabIndex={0}
            onKeyDown={(e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                onSelectFilter && onSelectFilter(stat.filterType);
              }
            }}
          >
            <div className="stat-header">
              <span className="stat-label">{stat.label}</span>
              <div className="stat-icon-wrapper">
                <IconComponent size={20} className="stat-icon" />
              </div>
            </div>
            <div className="stat-body">
              <span className="stat-value">{stat.value}</span>
            </div>
            <div className="stat-footer">
              <span className="stat-desc">{stat.description}</span>
            </div>
          </div>
        );
      })}
    </div>
  );
}
