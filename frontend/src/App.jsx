import React, { useState, useEffect, useMemo } from 'react';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';

// API Base URL - uses relative path in production, localhost in dev
const API_BASE = import.meta.env.PROD ? '/api' : 'http://localhost:5000/api';

// Color palette
const COLORS = {
  theft: '#3b82f6',
  robbery: '#ef4444',
  burglary: '#f97316',
  assault: '#dc2626',
  fraud: '#8b5cf6',
  vandalism: '#eab308',
  other: '#64748b',
  orc: '#ec4899',
  smash_grab: '#f43f5e',
  shoplifting: '#06b6d4'
};

const SEVERITY_COLORS = ['#22c55e', '#84cc16', '#eab308', '#f97316', '#ef4444'];

// Stat Card Component
function StatCard({ title, value, subtitle, trend, icon }) {
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
      <div className="flex justify-between items-start">
        <div>
          <p className="text-slate-400 text-sm">{title}</p>
          <p className="text-2xl font-bold text-white mt-1">{value?.toLocaleString() || '—'}</p>
          {subtitle && <p className="text-slate-500 text-xs mt-1">{subtitle}</p>}
        </div>
        {icon && <span className="text-2xl">{icon}</span>}
      </div>
      {trend !== undefined && (
        <div className={`text-sm mt-2 ${trend >= 0 ? 'text-red-400' : 'text-green-400'}`}>
          {trend >= 0 ? '↑' : '↓'} {Math.abs(trend)}% vs last period
        </div>
      )}
    </div>
  );
}

// Filter Panel Component
function FilterPanel({ filters, setFilters, locations, incidentTypes }) {
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
      <h3 className="text-lg font-semibold mb-4">Filters</h3>

      <div className="space-y-4">
        {/* Country Filter */}
        <div>
          <label className="block text-sm text-slate-400 mb-1">Country</label>
          <select
            className="w-full bg-slate-700 border border-slate-600 rounded px-3 py-2 text-white"
            value={filters.country || ''}
            onChange={(e) => setFilters({...filters, country: e.target.value || null, state: null, city: null})}
          >
            <option value="">All Countries</option>
            {Object.keys(locations).map(country => (
              <option key={country} value={country}>{country}</option>
            ))}
          </select>
        </div>

        {/* State Filter */}
        {filters.country && locations[filters.country] && (
          <div>
            <label className="block text-sm text-slate-400 mb-1">State/Province</label>
            <select
              className="w-full bg-slate-700 border border-slate-600 rounded px-3 py-2 text-white"
              value={filters.state || ''}
              onChange={(e) => setFilters({...filters, state: e.target.value || null, city: null})}
            >
              <option value="">All States</option>
              {Object.keys(locations[filters.country]).map(state => (
                <option key={state} value={state}>{state}</option>
              ))}
            </select>
          </div>
        )}

        {/* City Filter */}
        {filters.state && locations[filters.country]?.[filters.state] && (
          <div>
            <label className="block text-sm text-slate-400 mb-1">City</label>
            <select
              className="w-full bg-slate-700 border border-slate-600 rounded px-3 py-2 text-white"
              value={filters.city || ''}
              onChange={(e) => setFilters({...filters, city: e.target.value || null})}
            >
              <option value="">All Cities</option>
              {locations[filters.country][filters.state].map(city => (
                <option key={city} value={city}>{city}</option>
              ))}
            </select>
          </div>
        )}

        {/* Incident Type Filter */}
        <div>
          <label className="block text-sm text-slate-400 mb-1">Incident Type</label>
          <select
            className="w-full bg-slate-700 border border-slate-600 rounded px-3 py-2 text-white"
            value={filters.type || ''}
            onChange={(e) => setFilters({...filters, type: e.target.value || null})}
          >
            <option value="">All Types</option>
            {incidentTypes.map(type => (
              <option key={type} value={type}>{type}</option>
            ))}
          </select>
        </div>

        {/* Severity Filter */}
        <div>
          <label className="block text-sm text-slate-400 mb-1">Min Severity</label>
          <select
            className="w-full bg-slate-700 border border-slate-600 rounded px-3 py-2 text-white"
            value={filters.min_severity || ''}
            onChange={(e) => setFilters({...filters, min_severity: e.target.value ? parseInt(e.target.value) : null})}
          >
            <option value="">All</option>
            <option value="2">2+ (Low)</option>
            <option value="3">3+ (Medium)</option>
            <option value="4">4+ (High)</option>
            <option value="5">5 (Critical)</option>
          </select>
        </div>

        {/* Time Range */}
        <div>
          <label className="block text-sm text-slate-400 mb-1">Time Range</label>
          <select
            className="w-full bg-slate-700 border border-slate-600 rounded px-3 py-2 text-white"
            value={filters.days || 30}
            onChange={(e) => setFilters({...filters, days: parseInt(e.target.value)})}
          >
            <option value={7}>Last 7 days</option>
            <option value={30}>Last 30 days</option>
            <option value={60}>Last 60 days</option>
            <option value={90}>Last 90 days</option>
          </select>
        </div>

        {/* Clear Filters */}
        <button
          className="w-full bg-slate-600 hover:bg-slate-500 text-white py-2 rounded transition"
          onClick={() => setFilters({ days: 30 })}
        >
          Clear Filters
        </button>
      </div>
    </div>
  );
}

// Trend Chart Component
function TrendChart({ data, title }) {
  const chartData = useMemo(() => {
    if (!data?.trends) return [];
    return data.trends.slice(-30);
  }, [data]);

  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
      <h3 className="text-lg font-semibold mb-4">{title}</h3>
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis
              dataKey="period"
              stroke="#64748b"
              tick={{ fill: '#94a3b8' }}
              tickFormatter={(value) => value?.slice(5) || ''}
            />
            <YAxis stroke="#64748b" tick={{ fill: '#94a3b8' }} />
            <Tooltip
              contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155' }}
              labelStyle={{ color: '#e2e8f0' }}
            />
            <Legend />
            <Line type="monotone" dataKey="total" name="Total" stroke="#3b82f6" strokeWidth={2} dot={false} />
            <Line type="monotone" dataKey="theft" name="Theft" stroke={COLORS.theft} strokeWidth={1} dot={false} />
            <Line type="monotone" dataKey="robbery" name="Robbery" stroke={COLORS.robbery} strokeWidth={1} dot={false} />
            <Line type="monotone" dataKey="assault" name="Assault" stroke={COLORS.assault} strokeWidth={1} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

// Incident Type Distribution Chart
function TypeDistributionChart({ stats }) {
  const chartData = useMemo(() => {
    if (!stats?.by_type) return [];
    return Object.entries(stats.by_type).slice(0, 8).map(([name, value]) => ({
      name,
      value,
      color: COLORS[name] || COLORS.other
    }));
  }, [stats]);

  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
      <h3 className="text-lg font-semibold mb-4">Incidents by Type</h3>
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData} layout="vertical">
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis type="number" stroke="#64748b" tick={{ fill: '#94a3b8' }} />
            <YAxis type="category" dataKey="name" stroke="#64748b" tick={{ fill: '#94a3b8' }} width={80} />
            <Tooltip
              contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155' }}
              labelStyle={{ color: '#e2e8f0' }}
            />
            <Bar dataKey="value" name="Incidents">
              {chartData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

// Incident Feed Component
function IncidentFeed({ incidents, loading }) {
  const getSeverityColor = (severity) => {
    const colors = ['', 'bg-green-500', 'bg-lime-500', 'bg-yellow-500', 'bg-orange-500', 'bg-red-500'];
    return colors[severity] || 'bg-slate-500';
  };

  if (loading) {
    return (
      <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
        <h3 className="text-lg font-semibold mb-4">Recent Incidents</h3>
        <div className="animate-pulse space-y-3">
          {[1,2,3,4,5].map(i => (
            <div key={i} className="h-16 bg-slate-700 rounded"></div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
      <h3 className="text-lg font-semibold mb-4">Recent Incidents</h3>
      <div className="space-y-2 max-h-96 overflow-y-auto custom-scrollbar">
        {incidents?.map((incident, idx) => (
          <div key={incident.id || idx} className="bg-slate-700/50 rounded p-3 hover:bg-slate-700 transition">
            <div className="flex items-start justify-between">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className={`w-2 h-2 rounded-full ${getSeverityColor(incident.severity)}`}></span>
                  <span className="text-sm font-medium text-slate-300 truncate">
                    {incident.title || incident.incident_type || 'Incident'}
                  </span>
                </div>
                <p className="text-xs text-slate-400 mt-1 line-clamp-2">
                  {incident.description?.slice(0, 120) || 'No description'}
                  {incident.description?.length > 120 ? '...' : ''}
                </p>
                <div className="flex items-center gap-2 mt-2 text-xs text-slate-500">
                  <span>{incident.city || incident.state_province || incident.country || 'Unknown'}</span>
                  <span>•</span>
                  <span>{incident.incident_date}</span>
                  {incident.source_name && (
                    <>
                      <span>•</span>
                      <span>{incident.source_name}</span>
                    </>
                  )}
                </div>
              </div>
              <span className="text-xs px-2 py-1 rounded bg-slate-600 text-slate-300 ml-2 whitespace-nowrap">
                {incident.incident_type || 'unknown'}
              </span>
            </div>
          </div>
        ))}
        {(!incidents || incidents.length === 0) && (
          <p className="text-slate-500 text-center py-4">No incidents found</p>
        )}
      </div>
    </div>
  );
}

// Simple Map Component (using an iframe for OpenStreetMap as a fallback)
function SimpleMap({ mapData }) {
  const [selectedCluster, setSelectedCluster] = useState(null);

  // Create a simple visualization using CSS
  const maxCount = Math.max(...(mapData?.clusters?.map(c => c.incident_count) || [1]));

  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
      <h3 className="text-lg font-semibold mb-4">Geographic Distribution</h3>

      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2 max-h-80 overflow-y-auto custom-scrollbar">
        {mapData?.clusters?.slice(0, 20).map((cluster, idx) => {
          const intensity = cluster.incident_count / maxCount;
          const bgColor = intensity > 0.7 ? 'bg-red-600' : intensity > 0.4 ? 'bg-orange-500' : intensity > 0.2 ? 'bg-yellow-500' : 'bg-green-500';

          return (
            <div
              key={idx}
              className={`${bgColor} bg-opacity-20 border border-slate-600 rounded p-2 cursor-pointer hover:bg-opacity-40 transition`}
              onClick={() => setSelectedCluster(cluster)}
            >
              <p className="font-medium text-sm truncate">{cluster.city || cluster.state_province}</p>
              <p className="text-xs text-slate-400">{cluster.country}</p>
              <p className="text-lg font-bold">{cluster.incident_count.toLocaleString()}</p>
              <p className="text-xs text-slate-500">incidents</p>
            </div>
          );
        })}
      </div>

      {selectedCluster && (
        <div className="mt-4 p-3 bg-slate-700 rounded">
          <h4 className="font-semibold">{selectedCluster.city}, {selectedCluster.state_province}</h4>
          <p className="text-slate-400">{selectedCluster.country}</p>
          <p className="text-xl font-bold mt-2">{selectedCluster.incident_count.toLocaleString()} incidents</p>
          <p className="text-sm text-slate-400">Avg Severity: {selectedCluster.avg_severity?.toFixed(1) || 'N/A'}</p>
          {selectedCluster.latitude && (
            <a
              href={`https://www.google.com/maps?q=${selectedCluster.latitude},${selectedCluster.longitude}`}
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-400 hover:text-blue-300 text-sm mt-2 inline-block"
            >
              View on Google Maps →
            </a>
          )}
        </div>
      )}
    </div>
  );
}

// Data Source Status Component
function DataSourceStatus({ sources }) {
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
      <h3 className="text-lg font-semibold mb-4">Data Sources</h3>
      <div className="space-y-2">
        {sources?.map((source, idx) => (
          <div key={idx} className="flex items-center justify-between py-2 border-b border-slate-700 last:border-0">
            <div className="flex items-center gap-2">
              <span className={`w-2 h-2 rounded-full ${source.last_success ? 'bg-green-500' : 'bg-red-500'}`}></span>
              <span className="text-sm">{source.name}</span>
            </div>
            <div className="text-right">
              <p className="text-sm text-slate-400">{source.total_incidents?.toLocaleString() || 0} incidents</p>
              <p className="text-xs text-slate-500">
                {source.last_scraped ? new Date(source.last_scraped).toLocaleString() : 'Never'}
              </p>
            </div>
          </div>
        ))}
        {(!sources || sources.length === 0) && (
          <p className="text-slate-500 text-center py-4">No sources configured</p>
        )}
      </div>
    </div>
  );
}

// Main App Component
export default function App() {
  const [stats, setStats] = useState(null);
  const [trends, setTrends] = useState(null);
  const [incidents, setIncidents] = useState([]);
  const [mapData, setMapData] = useState(null);
  const [locations, setLocations] = useState({});
  const [incidentTypes, setIncidentTypes] = useState([]);
  const [sources, setSources] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [filters, setFilters] = useState({
    days: 30,
    country: null,
    state: null,
    city: null,
    type: null,
    min_severity: null
  });

  // Fetch data
  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError(null);

      try {
        // Build query params
        const params = new URLSearchParams();
        if (filters.country) params.append('country', filters.country);
        if (filters.state) params.append('state', filters.state);
        if (filters.city) params.append('city', filters.city);
        if (filters.type) params.append('type', filters.type);
        if (filters.min_severity) params.append('min_severity', filters.min_severity);
        params.append('days', filters.days);
        params.append('limit', 100);

        const queryString = params.toString();

        // Fetch all data in parallel
        const [statsRes, trendsRes, incidentsRes, mapRes, locationsRes, typesRes, sourcesRes] = await Promise.all([
          fetch(`${API_BASE}/stats`).then(r => r.json()).catch(() => null),
          fetch(`${API_BASE}/trends?${queryString}`).then(r => r.json()).catch(() => null),
          fetch(`${API_BASE}/incidents?${queryString}`).then(r => r.json()).catch(() => null),
          fetch(`${API_BASE}/map`).then(r => r.json()).catch(() => null),
          fetch(`${API_BASE}/locations`).then(r => r.json()).catch(() => ({})),
          fetch(`${API_BASE}/types`).then(r => r.json()).catch(() => ({ types: [] })),
          fetch(`${API_BASE}/sources`).then(r => r.json()).catch(() => ({ sources: [] }))
        ]);

        setStats(statsRes);
        setTrends(trendsRes);
        setIncidents(incidentsRes?.incidents || []);
        setMapData(mapRes);
        setLocations(locationsRes);
        setIncidentTypes(typesRes?.types || []);
        setSources(sourcesRes?.sources || []);

      } catch (err) {
        console.error('Error fetching data:', err);
        setError('Failed to connect to API. Make sure the backend server is running.');
      }

      setLoading(false);
    };

    fetchData();
  }, [filters]);

  return (
    <div className="min-h-screen bg-slate-900">
      {/* Header */}
      <header className="bg-slate-800 border-b border-slate-700 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-white">Retail Security Dashboard</h1>
            <p className="text-slate-400 text-sm">Real-time crime and security incident tracking</p>
          </div>
          <div className="flex items-center gap-4">
            <span className={`px-3 py-1 rounded-full text-sm ${error ? 'bg-red-900 text-red-300' : 'bg-green-900 text-green-300'}`}>
              {error ? '● Offline' : '● Connected'}
            </span>
            <span className="text-slate-400 text-sm">
              Last updated: {new Date().toLocaleTimeString()}
            </span>
                          <button
                                            onClick={async () => {
                                                                try {
                                                                                      const res = await fetch(`${API_BASE}/refresh`, { method: 'POST' });
                                                                                      const data = await res.json();
                                                                                      alert(data.message || data.error);
                                                                                      if (data.success) setTimeout(() => window.location.reload(), 3000);
                                                                } catch (e) { alert('Failed to trigger refresh'); }
                                            }}
                                            className="ml-4 px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded"
                                          >
                                          🔄 Refresh Data
                          </button>button></button>
          </div>
        </div>
      </header>

      {/* Error Banner */}
      {error && (
        <div className="bg-red-900/50 border-b border-red-800 px-6 py-3 text-red-200">
          {error}
          <span className="ml-2 text-red-300">Run: <code className="bg-red-800 px-2 py-1 rounded">python backend/api_server.py</code></span>
        </div>
      )}

      {/* Main Content */}
      <div className="flex">
        {/* Sidebar - Filters */}
        <aside className="w-64 p-4 border-r border-slate-700 min-h-screen">
          <FilterPanel
            filters={filters}
            setFilters={setFilters}
            locations={locations}
            incidentTypes={incidentTypes}
          />

          <div className="mt-4">
            <DataSourceStatus sources={sources} />
          </div>
        </aside>

        {/* Main Dashboard */}
        <main className="flex-1 p-6">
          {/* Stats Row */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            <StatCard
              title="Total Incidents"
              value={stats?.total_incidents}
              icon="📊"
            />
            <StatCard
              title="Last 7 Days"
              value={stats?.last_7_days}
              icon="📅"
            />
            <StatCard
              title="Last 30 Days"
              value={stats?.last_30_days}
              icon="📈"
            />
            <StatCard
              title="Data Sources"
              value={sources?.length}
              subtitle={`${sources?.filter(s => s.last_success).length || 0} active`}
              icon="🔗"
            />
          </div>

          {/* Charts Row */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
            <TrendChart data={trends} title="Incident Trends Over Time" />
            <TypeDistributionChart stats={stats} />
          </div>

          {/* Map and Feed Row */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <SimpleMap mapData={mapData} />
            <IncidentFeed incidents={incidents} loading={loading} />
          </div>
        </main>
      </div>
    </div>
  );
}
