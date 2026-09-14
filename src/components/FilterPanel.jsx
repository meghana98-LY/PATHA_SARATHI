import { RotateCcw, Search, SlidersHorizontal } from 'lucide-react';

export default function FilterPanel({ filters, onFilterChange, onResetFilters, incidentCount }) {
  return (
    <div className="filter-panel" aria-label="Incident Filter Controls">
      <div className="filter-panel-header">
        <div className="filter-title">
          <SlidersHorizontal size={18} className="filter-icon" />
          <span>Filters & Search</span>
        </div>
        <button
          type="button"
          className="reset-btn"
          onClick={onResetFilters}
          title="Reset all filters to default"
          aria-label="Reset all filters"
        >
          <RotateCcw size={14} />
          <span>Reset</span>
        </button>
      </div>

      <div className="filter-grid">
        {/* Search input */}
        <div className="filter-group filter-search">
          <label htmlFor="search-input" className="filter-label">
            Search
          </label>
          <div className="search-input-wrapper">
            <Search size={16} className="search-icon" />
            <input
              id="search-input"
              type="text"
              className="filter-input"
              placeholder="Search by ID, Bus, location..."
              value={filters.search}
              onChange={(e) => onFilterChange('search', e.target.value)}
            />
          </div>
        </div>

        {/* Hazard Type Filter */}
        <div className="filter-group">
          <label htmlFor="hazard-type-select" className="filter-label">
            Hazard Type
          </label>
          <select
            id="hazard-type-select"
            className="filter-select"
            value={filters.type}
            onChange={(e) => onFilterChange('type', e.target.value)}
          >
            <option value="all">All Types</option>
            <option value="pothole">Pothole</option>
            <option value="road_damage">Road Damage</option>
            <option value="road_obstruction">Road Obstruction</option>
          </select>
        </div>

        {/* Priority Filter */}
        <div className="filter-group">
          <label htmlFor="priority-select" className="filter-label">
            Priority
          </label>
          <select
            id="priority-select"
            className="filter-select"
            value={filters.priority}
            onChange={(e) => onFilterChange('priority', e.target.value)}
          >
            <option value="all">All Priorities</option>
            <option value="high">High Priority</option>
            <option value="medium">Medium Priority</option>
            <option value="low">Low Priority</option>
          </select>
        </div>

        {/* Status Filter */}
        <div className="filter-group">
          <label htmlFor="status-select" className="filter-label">
            Status
          </label>
          <select
            id="status-select"
            className="filter-select"
            value={filters.status}
            onChange={(e) => onFilterChange('status', e.target.value)}
          >
            <option value="all">All Statuses</option>
            <option value="pending">Pending</option>
            <option value="verified">Verified</option>
            <option value="in_progress">In Progress</option>
            <option value="resolved">Resolved</option>
          </select>
        </div>

        {/* Source Filter */}
        <div className="filter-group">
          <label htmlFor="source-select" className="filter-label">
            Source
          </label>
          <select
            id="source-select"
            className="filter-select"
            value={filters.source}
            onChange={(e) => onFilterChange('source', e.target.value)}
          >
            <option value="all">All Sources</option>
            <option value="bus">Public Bus</option>
            <option value="citizen">Citizen Report</option>
          </select>
        </div>
      </div>

      <div className="filter-summary">
        Showing <strong>{incidentCount}</strong> matching incident{incidentCount === 1 ? '' : 's'}
      </div>
    </div>
  );
}
