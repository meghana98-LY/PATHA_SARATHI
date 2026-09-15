import { useState, useEffect, useMemo } from 'react';
import {
  ShieldAlert,
  RefreshCw,
  Map as MapIcon,
  List,
  AlertCircle,
  Radio,
  Compass
} from 'lucide-react';

import Map from '../components/Map';
import Statistics from '../components/Statistics';
import FilterPanel from '../components/FilterPanel';
import IncidentCard from '../components/IncidentCard';
import IncidentDetails from '../components/IncidentDetails';
import AuthorityAlerts from '../components/AuthorityAlerts';

import {
  fetchIncidents,
  updateIncidentStatus,
  fetchAuthorityAlerts
} from '../services/api';

const DEFAULT_FILTERS = {
  type: 'all',
  priority: 'all',
  status: 'all',
  source: 'all',
  search: ''
};

export default function Dashboard() {
  const [incidents, setIncidents] = useState([]);
  const [alerts, setAlerts] = useState([]);

  const [loading, setLoading] = useState(true);
  const [alertsLoading, setAlertsLoading] = useState(true);
  const [error, setError] = useState(null);

  const [lastRefreshed, setLastRefreshed] = useState(null);

  const [filters, setFilters] = useState(DEFAULT_FILTERS);
  const [activeStatFilter, setActiveStatFilter] = useState('all');

  const [selectedIncident, setSelectedIncident] = useState(null);
  const [detailedIncident, setDetailedIncident] = useState(null);

  // Mobile layout tab toggle: 'map' or 'list'
  const [mobileTab, setMobileTab] = useState('map');

  // Load incidents and authority alerts on mount.
  useEffect(() => {
    let isMounted = true;

    const loadDashboardData = async () => {
      try {
        setLoading(true);
        setAlertsLoading(true);
        setError(null);

        const [incidentData, alertData] = await Promise.all([
          fetchIncidents(),
          fetchAuthorityAlerts()
        ]);

        if (isMounted) {
          setIncidents(incidentData);
          setAlerts(alertData);

          setLastRefreshed(
            new Date().toLocaleTimeString('en-IN', {
              hour: '2-digit',
              minute: '2-digit',
              second: '2-digit'
            })
          );
        }
      } catch (err) {
        if (isMounted) {
          console.error(
            'Error loading dashboard data:',
            err
          );
          setError(
            'Unable to load dashboard data from server.'
          );
        }
      } finally {
        if (isMounted) {
          setLoading(false);
          setAlertsLoading(false);
        }
      }
    };

    loadDashboardData();

    return () => {
      isMounted = false;
    };
  }, []);

  // Manual refresh handler.
  const handleManualRefresh = async () => {
    setLoading(true);
    setAlertsLoading(true);
    setError(null);

    try {
      const [incidentData, alertData] = await Promise.all([
        fetchIncidents(),
        fetchAuthorityAlerts()
      ]);

      setIncidents(incidentData);
      setAlerts(alertData);

      setLastRefreshed(
        new Date().toLocaleTimeString('en-IN', {
          hour: '2-digit',
          minute: '2-digit',
          second: '2-digit'
        })
      );
    } catch (err) {
      console.error(
        'Error loading dashboard data:',
        err
      );

      setError(
        'Unable to load dashboard data from server.'
      );
    } finally {
      setLoading(false);
      setAlertsLoading(false);
    }
  };

  // Handle incident filter changes.
  const handleFilterChange = (key, value) => {
    setFilters(prev => ({
      ...prev,
      [key]: value
    }));

    setActiveStatFilter('custom');
  };

  // Quick statistics filter.
  const handleStatFilterSelect = filterType => {
    setActiveStatFilter(filterType);

    if (filterType === 'all') {
      setFilters(DEFAULT_FILTERS);
    } else if (filterType === 'high_priority') {
      setFilters({
        ...DEFAULT_FILTERS,
        priority: 'high'
      });
    } else if (filterType === 'pending_status') {
      setFilters({
        ...DEFAULT_FILTERS,
        status: 'pending'
      });
    } else if (filterType === 'resolved_status') {
      setFilters({
        ...DEFAULT_FILTERS,
        status: 'resolved'
      });
    }
  };

  const handleResetFilters = () => {
    setFilters(DEFAULT_FILTERS);
    setActiveStatFilter('all');
  };

  // Incident status modification.
  const handleStatusChange = async (
    incidentId,
    newStatus
  ) => {
    try {
      await updateIncidentStatus(
        incidentId,
        newStatus
      );

      setIncidents(prev =>
        prev.map(item =>
          item.incident_id === incidentId
            ? {
                ...item,
                status: newStatus
              }
            : item
        )
      );

      if (
        detailedIncident &&
        detailedIncident.incident_id === incidentId
      ) {
        setDetailedIncident(prev => ({
          ...prev,
          status: newStatus
        }));
      }

      if (
        selectedIncident &&
        selectedIncident.incident_id === incidentId
      ) {
        setSelectedIncident(prev => ({
          ...prev,
          status: newStatus
        }));
      }
    } catch (e) {
      console.error(
        'Status update error:',
        e
      );
    }
  };

  // Authority alert status modification.
  const handleAuthorityAlertUpdated = updatedAlert => {
    setAlerts(prev =>
      prev.map(alert =>
        alert.alert_id === updatedAlert.alert_id
          ? updatedAlert
          : alert
      )
    );
  };

  // Filtered incidents calculation.
  const filteredIncidents = useMemo(() => {
    return incidents.filter(inc => {
      if (
        filters.type !== 'all' &&
        inc.type !== filters.type
      ) {
        return false;
      }

      if (
        filters.priority !== 'all' &&
        inc.priority !== filters.priority
      ) {
        return false;
      }

      if (
        filters.status !== 'all' &&
        inc.status !== filters.status
      ) {
        return false;
      }

      if (
        filters.source !== 'all' &&
        inc.source !== filters.source
      ) {
        return false;
      }

      if (filters.search.trim() !== '') {
        const query =
          filters.search.toLowerCase();

        const matchesId =
          inc.incident_id
            ?.toLowerCase()
            .includes(query);

        const matchesBus =
          inc.bus_id
            ?.toLowerCase()
            .includes(query);

        const matchesType =
          inc.type
            ?.toLowerCase()
            .includes(query);

        const matchesLocation =
          inc.location_name
            ?.toLowerCase()
            .includes(query);

        if (
          !matchesId &&
          !matchesBus &&
          !matchesType &&
          !matchesLocation
        ) {
          return false;
        }
      }

      return true;
    });
  }, [incidents, filters]);

  return (
    <div className="dashboard-container">

      {/* Top Header */}
      <header className="dashboard-header">
        <div className="header-brand">
          <div className="brand-logo">
            <ShieldAlert
              size={28}
              className="logo-icon"
            />
          </div>

          <div className="brand-text">
            <h1>PATHA SARATHI</h1>
            <span className="brand-subtitle">
              GIS Road Hazard & Incident Command Center
            </span>
          </div>
        </div>

        <div className="header-controls">
          <div className="live-status-indicator">
            <Radio
              size={14}
              className="pulse-icon text-emerald"
            />

            <span>LIVE SYNC</span>

            {lastRefreshed && (
              <span className="refresh-time">
                ({lastRefreshed})
              </span>
            )}
          </div>

          <button
            type="button"
            className="header-refresh-btn"
            onClick={handleManualRefresh}
            disabled={loading || alertsLoading}
            title="Refresh Dashboard Data"
          >
            <RefreshCw
              size={16}
              className={
                loading || alertsLoading
                  ? 'spin'
                  : ''
              }
            />

            <span>Refresh</span>
          </button>
        </div>
      </header>

      {/* Main Content */}
      <main className="dashboard-main">

        {/* Statistics */}
        <Statistics
          incidents={incidents}
          activeFilter={activeStatFilter}
          onSelectFilter={
            handleStatFilterSelect
          }
        />

        {/* Authority Alerts */}
        <AuthorityAlerts
          alerts={alerts}
          loading={alertsLoading}
          onAlertUpdated={
            handleAuthorityAlertUpdated
          }
        />

        {/* Loading / Error States */}
        {error && (
          <div className="dashboard-banner banner-error">
            <AlertCircle size={20} />
            <span>{error}</span>
          </div>
        )}

        {/* Mobile View Toggle */}
        <div
          className="mobile-view-tabs"
          role="tablist"
          aria-label="Dashboard Views"
        >
          <button
            type="button"
            role="tab"
            aria-selected={
              mobileTab === 'map'
            }
            className={`tab-btn ${
              mobileTab === 'map'
                ? 'active'
                : ''
            }`}
            onClick={() =>
              setMobileTab('map')
            }
          >
            <MapIcon size={16} />
            GIS Map
          </button>

          <button
            type="button"
            role="tab"
            aria-selected={
              mobileTab === 'list'
            }
            className={`tab-btn ${
              mobileTab === 'list'
                ? 'active'
                : ''
            }`}
            onClick={() =>
              setMobileTab('list')
            }
          >
            <List size={16} />
            Incident List (
            {filteredIncidents.length}
            )
          </button>
        </div>

        {/* Desktop Split Layout */}
        <div className="dashboard-grid">

          {/* Left Column */}
          <div
            className={`dashboard-sidebar ${
              mobileTab === 'list'
                ? 'mobile-visible'
                : ''
            }`}
          >
            <FilterPanel
              filters={filters}
              onFilterChange={
                handleFilterChange
              }
              onResetFilters={
                handleResetFilters
              }
              incidentCount={
                filteredIncidents.length
              }
            />

            <div className="incident-list-container">
              <div className="list-header">
                <h3>Incident Reports</h3>

                <span className="count-pill">
                  {filteredIncidents.length} items
                </span>
              </div>

              {loading ? (
                <div className="list-loading">
                  <RefreshCw
                    size={24}
                    className="spin text-accent"
                  />

                  <p>
                    Loading GIS hazard reports...
                  </p>
                </div>
              ) : filteredIncidents.length ===
                0 ? (
                <div className="list-empty">
                  <Compass
                    size={32}
                    className="text-muted"
                  />

                  <p>
                    No incidents match the
                    selected filter criteria.
                  </p>

                  <button
                    type="button"
                    className="btn-inline"
                    onClick={
                      handleResetFilters
                    }
                  >
                    Clear Filters
                  </button>
                </div>
              ) : (
                <div className="incident-cards-scroll">
                  {filteredIncidents.map(
                    incident => (
                      <IncidentCard
                        key={
                          incident.incident_id
                        }
                        incident={incident}
                        isSelected={
                          selectedIncident?.incident_id ===
                          incident.incident_id
                        }
                        onSelect={inc => {
                          setSelectedIncident(
                            inc
                          );

                          setDetailedIncident(
                            inc
                          );

                          if (
                            window.innerWidth <=
                            768
                          ) {
                            setMobileTab(
                              'map'
                            );
                          }
                        }}
                      />
                    )
                  )}
                </div>
              )}
            </div>
          </div>

          {/* Right Column */}
          <div
            className={`dashboard-map-area ${
              mobileTab === 'map'
                ? 'mobile-visible'
                : ''
            }`}
          >
            <Map
              incidents={
                filteredIncidents
              }
              selectedIncident={
                selectedIncident
              }
              onSelectIncident={inc =>
                setSelectedIncident(inc)
              }
              onViewDetails={inc =>
                setDetailedIncident(inc)
              }
            />
          </div>
        </div>
      </main>

      {/* Incident Details Modal */}
      {detailedIncident && (
        <IncidentDetails
          incident={detailedIncident}
          onClose={() =>
            setDetailedIncident(null)
          }
          onStatusChange={
            handleStatusChange
          }
          onFocusMap={inc => {
            setSelectedIncident(inc);
            setDetailedIncident(null);
            setMobileTab('map');
          }}
        />
      )}
    </div>
  );
}