import { useEffect, useState } from 'react';
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import * as api from '../api.js';
import { buildFilterParams } from '../filters.js';

const SENTIMENT_COLORS = { positive: '#48bb78', neutral: '#a0aec0', negative: '#f56565' };
const RATING_COLORS = ['#f56565', '#ed8936', '#ecc94b', '#9ae6b4', '#48bb78'];

const EMPTY_FILTERS = { q: '', rating: '', sentiment: '', start_date: '', end_date: '' };

export default function DashboardPage() {
  const [apps, setApps] = useState([]);
  const [appId, setAppId] = useState(null);
  const [stats, setStats] = useState(null);
  const [reviews, setReviews] = useState({ total: 0, items: [] });
  const [filters, setFilters] = useState(EMPTY_FILTERS);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    api.listApps()
      .then((rows) => {
        setApps(rows);
        if (rows.length > 0) setAppId(rows[0].id);
      })
      .catch((err) => setError(err.message));
  }, []);

  useEffect(() => {
    if (!appId) return;
    setLoading(true);
    api.getStats(appId)
      .then(setStats)
      .catch((err) => setError(err.message));
    
    loadReviews(appId, {});
  }, [appId]);

  async function loadReviews(id, params) {
    try {
      const data = await api.getReviews(id, params);
      setReviews(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  function applyFilters(event) {
    event.preventDefault();
    setLoading(true);
    const params = buildFilterParams(filters);
    loadReviews(appId, { ...params, page: 1, page_size: 100 });
  }

  function clearFilters() {
    setFilters(EMPTY_FILTERS);
    setLoading(true);
    loadReviews(appId, {});
  }

  const selectedApp = apps.find((a) => a.id === appId);

  // Normalize rating distribution to ensure all 5 stars exist
  const ratingData = [1, 2, 3, 4, 5].map((star) => {
    const found = stats?.rating_distribution.find((d) => d.rating === star);
    return { rating: `${star}★`, count: found ? found.count : 0 };
  });

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24, flexWrap: 'wrap', gap: 16 }}>
        <div>
          <h1 style={{ margin: '0 0 4px 0', fontSize: '28px', color: '#1a365d' }}>Dashboard</h1>
          <p style={{ margin: 0, color: '#718096', fontSize: '15px' }}>Analyze fetched app ratings, trends, and review contents.</p>
        </div>
        {apps.length > 0 && (
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <label htmlFor="app-select" style={{ fontWeight: '600', color: '#4a5568', fontSize: '14px' }}>Select App:</label>
            <select 
              id="app-select"
              value={appId || ''} 
              onChange={(e) => setAppId(Number(e.target.value))} 
              style={{ 
                padding: '8px 16px', 
                fontSize: '15px', 
                borderRadius: 6, 
                border: '1px solid #cbd5e0',
                backgroundColor: '#fff',
                outline: 'none',
                fontWeight: '500',
                color: '#2d3748'
              }}
            >
              {apps.map((a) => (
                <option key={a.id} value={a.id}>
                  {a.name} ({a.platform === 'playstore' ? 'Google Play' : 'App Store'})
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      {apps.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '48px 0', color: '#718096' }}>
          <p style={{ fontSize: '18px', fontWeight: '500', margin: '0 0 12px 0' }}>No apps imported yet.</p>
          <p style={{ margin: 0, fontSize: '14px' }}>Head over to the "Search &amp; Fetch" page to import reviews for an app!</p>
        </div>
      ) : (
        <>
          {stats && (
            <>
              {/* Stat Cards */}
              <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', marginBottom: 24 }}>
                <StatCard label="Total Reviews" value={stats.total_reviews} icon="💬" />
                <StatCard label="Average Rating" value={stats.avg_rating?.toFixed(2) ?? '—'} icon="⭐" />
                <StatCard 
                  label="Positive Reviews" 
                  value={stats.sentiment_breakdown.find((s) => s.label === 'positive')?.count ?? 0} 
                  icon="🟢" 
                />
                <StatCard 
                  label="Negative Reviews" 
                  value={stats.sentiment_breakdown.find((s) => s.label === 'negative')?.count ?? 0} 
                  icon="🔴" 
                />
              </div>

              {/* Charts Row */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: 20, marginBottom: 32 }}>
                <ChartBox title="Rating Distribution">
                  <BarChart data={ratingData}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} />
                    <XAxis dataKey="rating" axisLine={false} tickLine={false} />
                    <YAxis allowDecimals={false} axisLine={false} tickLine={false} />
                    <Tooltip />
                    <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                      {ratingData.map((entry, i) => (
                        <Cell key={i} fill={RATING_COLORS[i]} />
                      ))}
                    </Bar>
                  </BarChart>
                </ChartBox>

                <ChartBox title="Review Volume Trends">
                  {stats.volume_over_time.length > 0 ? (
                    <LineChart data={stats.volume_over_time}>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} />
                      <XAxis dataKey="month" axisLine={false} tickLine={false} />
                      <YAxis allowDecimals={false} axisLine={false} tickLine={false} />
                      <Tooltip />
                      <Line type="monotone" dataKey="count" stroke="#3182ce" strokeWidth={3} activeDot={{ r: 8 }} />
                    </LineChart>
                  ) : (
                    <div style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#a0aec0', fontSize: '14px' }}>
                      No date data available
                    </div>
                  )}
                </ChartBox>

                <ChartBox title="Sentiment Split">
                  <PieChart>
                    <Pie 
                      data={stats.sentiment_breakdown} 
                      dataKey="count" 
                      nameKey="label" 
                      outerRadius={80}
                      innerRadius={50}
                      paddingAngle={3}
                    >
                      {stats.sentiment_breakdown.map((s, i) => (
                        <Cell key={i} fill={SENTIMENT_COLORS[s.label] ?? '#bdc3c7'} />
                      ))}
                    </Pie>
                    <Tooltip />
                    <Legend verticalAlign="bottom" height={36} />
                  </PieChart>
                </ChartBox>
              </div>
            </>
          )}

          {/* Filters Form */}
          <div style={{ backgroundColor: '#f8f9fa', border: '1px solid #e2e8f0', borderRadius: 8, padding: 16, marginBottom: 24 }}>
            <h3 style={{ margin: '0 0 12px 0', fontSize: '16px', color: '#2d3748' }}>Filter Reviews</h3>
            <form onSubmit={applyFilters} style={{ display: 'flex', gap: 12, flexWrap: 'wrap', alignItems: 'flex-end' }}>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 4, flex: '1 1 200px' }}>
                <label style={{ fontSize: '13px', fontWeight: '600', color: '#4a5568' }}>Keyword</label>
                <input 
                  value={filters.q} 
                  onChange={(e) => setFilters({ ...filters, q: e.target.value })} 
                  placeholder="Search reviews content..."
                  style={{ padding: '8px 12px', fontSize: '14px', borderRadius: 6, border: '1px solid #cbd5e0', outline: 'none' }}
                />
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 4, width: '100px' }}>
                <label style={{ fontSize: '13px', fontWeight: '600', color: '#4a5568' }}>Rating</label>
                <select 
                  value={filters.rating} 
                  onChange={(e) => setFilters({ ...filters, rating: e.target.value })} 
                  style={{ padding: '8px 12px', fontSize: '14px', borderRadius: 6, border: '1px solid #cbd5e0', outline: 'none', backgroundColor: '#fff' }}
                >
                  <option value="">Any</option>
                  {[5, 4, 3, 2, 1].map((n) => (
                    <option key={n} value={n}>{n} ★</option>
                  ))}
                </select>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 4, width: '120px' }}>
                <label style={{ fontSize: '13px', fontWeight: '600', color: '#4a5568' }}>Sentiment</label>
                <select 
                  value={filters.sentiment} 
                  onChange={(e) => setFilters({ ...filters, sentiment: e.target.value })} 
                  style={{ padding: '8px 12px', fontSize: '14px', borderRadius: 6, border: '1px solid #cbd5e0', outline: 'none', backgroundColor: '#fff' }}
                >
                  <option value="">Any</option>
                  <option value="positive">Positive</option>
                  <option value="neutral">Neutral</option>
                  <option value="negative">Negative</option>
                </select>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 4, width: '130px' }}>
                <label style={{ fontSize: '13px', fontWeight: '600', color: '#4a5568' }}>From Date</label>
                <input 
                  type="date" 
                  value={filters.start_date} 
                  onChange={(e) => setFilters({ ...filters, start_date: e.target.value })} 
                  style={{ padding: '6px 12px', fontSize: '14px', borderRadius: 6, border: '1px solid #cbd5e0', outline: 'none' }}
                />
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 4, width: '130px' }}>
                <label style={{ fontSize: '13px', fontWeight: '600', color: '#4a5568' }}>To Date</label>
                <input 
                  type="date" 
                  value={filters.end_date} 
                  onChange={(e) => setFilters({ ...filters, end_date: e.target.value })} 
                  style={{ padding: '6px 12px', fontSize: '14px', borderRadius: 6, border: '1px solid #cbd5e0', outline: 'none' }}
                />
              </div>
              <div style={{ display: 'flex', gap: 8 }}>
                <button type="submit" style={{ padding: '8px 16px', fontSize: '14px', fontWeight: '600', color: '#fff', backgroundColor: '#3182ce', border: 'none', borderRadius: 6, cursor: 'pointer' }}>
                  Filter
                </button>
                <button type="button" onClick={clearFilters} style={{ padding: '8px 16px', fontSize: '14px', fontWeight: '600', color: '#4a5568', backgroundColor: '#edf2f7', border: 'none', borderRadius: 6, cursor: 'pointer' }}>
                  Reset
                </button>
              </div>
            </form>
          </div>

          {/* Export Actions & Summary */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16, flexWrap: 'wrap', gap: 12 }}>
            <div style={{ fontSize: '14px', color: '#4a5568', fontWeight: '500' }}>
              Showing {reviews.items.length} of {reviews.total} matching reviews
            </div>
            <div style={{ display: 'flex', gap: 12 }}>
              <a 
                href={api.exportUrl(appId, 'csv', buildFilterParams(filters))} 
                download 
                style={{ 
                  textDecoration: 'none', 
                  color: '#2b6cb0', 
                  backgroundColor: '#ebf8ff', 
                  padding: '6px 12px', 
                  borderRadius: 6, 
                  fontSize: '13px', 
                  fontWeight: '600',
                  border: '1px solid #bee3f8'
                }}
              >
                📥 Export CSV
              </a>
              <a 
                href={api.exportUrl(appId, 'json', buildFilterParams(filters))} 
                download 
                style={{ 
                  textDecoration: 'none', 
                  color: '#2c5282', 
                  backgroundColor: '#f7fafc', 
                  padding: '6px 12px', 
                  borderRadius: 6, 
                  fontSize: '13px', 
                  fontWeight: '600',
                  border: '1px solid #e2e8f0'
                }}
              >
                📥 Export JSON
              </a>
            </div>
          </div>

          {/* Reviews Table */}
          {loading ? (
            <div style={{ textAlign: 'center', padding: '40px 0', color: '#718096' }}>Loading reviews...</div>
          ) : reviews.items.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '40px 0', color: '#718096', border: '1px solid #e2e8f0', borderRadius: 8 }}>
              No reviews match the selected filter criteria.
            </div>
          ) : (
            <div style={{ overflowX: 'auto', border: '1px solid #e2e8f0', borderRadius: 8 }}>
              <table style={{ borderCollapse: 'collapse', width: '100%', margin: 0, fontSize: '14px' }}>
                <thead>
                  <tr style={{ backgroundColor: '#edf2f7', borderBottom: '2px solid #e2e8f0', textAlign: 'left' }}>
                    <th style={{ padding: '12px 16px', color: '#4a5568', fontWeight: '600', width: '110px' }}>Rating</th>
                    <th style={{ padding: '12px 16px', color: '#4a5568', fontWeight: '600', width: '120px' }}>Sentiment</th>
                    <th style={{ padding: '12px 16px', color: '#4a5568', fontWeight: '600', width: '140px' }}>User / Date</th>
                    <th style={{ padding: '12px 16px', color: '#4a5568', fontWeight: '600' }}>Review Title &amp; Body</th>
                  </tr>
                </thead>
                <tbody>
                  {reviews.items.map((r) => (
                    <tr key={r.id} style={{ borderBottom: '1px solid #e2e8f0', verticalAlign: 'top', backgroundColor: '#fff' }}>
                      <td style={{ padding: '12px 16px', color: '#d69e2e', whiteSpace: 'nowrap' }}>
                        {'★'.repeat(r.rating)}
                        <span style={{ color: '#cbd5e0' }}>{'★'.repeat(5 - r.rating)}</span>
                      </td>
                      <td style={{ padding: '12px 16px' }}>
                        <span style={{ 
                          padding: '3px 8px', 
                          borderRadius: 12, 
                          fontSize: '11px', 
                          fontWeight: '700',
                          textTransform: 'uppercase',
                          backgroundColor: r.sentiment_label === 'positive' ? '#c6f6d5' : r.sentiment_label === 'negative' ? '#fed7d7' : '#edf2f7',
                          color: r.sentiment_label === 'positive' ? '#22543d' : r.sentiment_label === 'negative' ? '#742a2a' : '#4a5568'
                        }}>
                          {r.sentiment_label}
                        </span>
                      </td>
                      <td style={{ padding: '12px 16px', color: '#2d3748' }}>
                        <div style={{ fontWeight: '600', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: '120px' }}>{r.author}</div>
                        <div style={{ fontSize: '12px', color: '#718096', marginTop: 2 }}>{r.created_at ? r.created_at.slice(0, 10) : '—'}</div>
                        {r.version && <div style={{ fontSize: '11px', color: '#a0aec0', marginTop: 1 }}>v{r.version}</div>}
                      </td>
                      <td style={{ padding: '12px 16px' }}>
                        {r.title && <div style={{ fontWeight: '700', color: '#1a202c', marginBottom: 4 }}>{r.title}</div>}
                        <div style={{ color: '#4a5568', lineHeight: '1.5', whiteSpace: 'pre-line' }}>{r.body}</div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}
      {error && <p style={{ color: '#e53e3e', marginTop: 16 }}>{error}</p>}
    </div>
  );
}

function StatCard({ label, value, icon }) {
  return (
    <div style={{ 
      border: '1px solid #e2e8f0', 
      borderRadius: 8, 
      padding: 16, 
      minWidth: '200px', 
      flex: '1 1 0',
      backgroundColor: '#fff', 
      boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
      display: 'flex',
      alignItems: 'center',
      gap: 16
    }}>
      <div style={{ fontSize: '28px' }}>{icon}</div>
      <div>
        <div style={{ fontSize: '24px', fontWeight: '700', color: '#2d3748', lineHeight: '1.2' }}>{value}</div>
        <div style={{ color: '#718096', fontSize: '13px', fontWeight: '500', marginTop: 2 }}>{label}</div>
      </div>
    </div>
  );
}

function ChartBox({ title, children }) {
  return (
    <div style={{ 
      border: '1px solid #e2e8f0', 
      borderRadius: 8, 
      padding: 16, 
      backgroundColor: '#fff', 
      boxShadow: '0 1px 3px rgba(0,0,0,0.05)' 
    }}>
      <h3 style={{ margin: '0 0 16px 0', fontSize: '16px', color: '#2d3748', fontWeight: '600' }}>{title}</h3>
      <div style={{ width: '100%', height: 220 }}>
        <ResponsiveContainer width="100%" height="100%">
          {children}
        </ResponsiveContainer>
      </div>
    </div>
  );
}
