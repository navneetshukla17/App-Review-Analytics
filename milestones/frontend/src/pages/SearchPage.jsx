import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import * as api from '../api.js';

const PLATFORM_LABELS = { playstore: 'Google Play Store', appstore: 'App Store' };

export default function SearchPage() {
  const [query, setQuery] = useState('');
  const [platform, setPlatform] = useState('both');
  const [results, setResults] = useState([]);
  const [errors, setErrors] = useState([]);
  const [searching, setSearching] = useState(false);
  const [job, setJob] = useState(null);
  const navigate = useNavigate();

  async function handleSearch(event) {
    event.preventDefault();
    if (!query.trim()) return;
    setSearching(true);
    setErrors([]);
    setJob(null);
    try {
      const data = await api.searchApps(query.trim(), platform);
      setResults(data.results);
      setErrors(data.errors || []);
    } catch (err) {
      setErrors([{ message: err.message }]);
      setResults([]);
    } finally {
      setSearching(false);
    }
  }

  async function handleFetch(candidate) {
    setJob({ status: 'starting', fetched_count: 0 });
    setErrors([]);
    try {
      const app = await api.createApp(candidate);
      const created = await api.startFetch(app.id);
      pollJob(created.id);
    } catch (err) {
      setErrors([{ message: err.message }]);
      setJob(null);
    }
  }

  async function pollJob(jobId) {
    try {
      const state = await api.getJob(jobId);
      setJob(state);
      if (state.status === 'running') {
        setTimeout(() => pollJob(jobId), 1500);
      } else if (state.status === 'completed') {
        setTimeout(() => navigate('/dashboard'), 600);
      } else if (state.status === 'failed') {
        setErrors([{ message: `Fetch job failed: ${state.message || 'unknown error'}` }]);
      }
    } catch {
      setTimeout(() => pollJob(jobId), 2000);
    }
  }

  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ margin: '0 0 8px 0', fontSize: '28px', color: '#1a365d' }}>Search &amp; Fetch reviews</h1>
        <p style={{ margin: 0, color: '#718096', fontSize: '15px' }}>
          Enter the name of any app to search the Google Play Store and Apple App Store, then fetch and analyze all its reviews for the India locale.
        </p>
      </div>

      <form 
        onSubmit={handleSearch} 
        style={{ 
          display: 'flex', 
          gap: 16, 
          flexWrap: 'wrap', 
          padding: 16, 
          backgroundColor: '#f7fafc', 
          borderRadius: 8, 
          border: '1px solid #e2e8f0',
          alignItems: 'flex-end',
          marginBottom: 24
        }}
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: 6, flex: '1 1 300px' }}>
          <label htmlFor="app-name-input" style={{ fontSize: '14px', fontWeight: '600', color: '#4a5568' }}>App Name</label>
          <input
            id="app-name-input"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="e.g. Spotify, Instagram, WhatsApp"
            style={{ 
              padding: '10px 14px', 
              fontSize: '15px', 
              borderRadius: 6, 
              border: '1px solid #cbd5e0',
              outline: 'none',
              transition: 'border-color 0.2s'
            }}
          />
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 6, width: '180px' }}>
          <label htmlFor="platform-select" style={{ fontSize: '14px', fontWeight: '600', color: '#4a5568' }}>Platform</label>
          <select 
            id="platform-select"
            value={platform} 
            onChange={(e) => setPlatform(e.target.value)} 
            style={{ 
              padding: '10px 14px', 
              fontSize: '15px', 
              borderRadius: 6, 
              border: '1px solid #cbd5e0',
              backgroundColor: '#fff',
              outline: 'none'
            }}
          >
            <option value="both">Both Stores</option>
            <option value="playstore">Play Store Only</option>
            <option value="appstore">App Store Only</option>
          </select>
        </div>
        <button 
          type="submit" 
          disabled={searching}
          style={{ 
            padding: '10px 24px', 
            fontSize: '15px', 
            fontWeight: '600',
            color: '#fff',
            backgroundColor: searching ? '#a0aec0' : '#3182ce',
            border: 'none',
            borderRadius: 6,
            cursor: searching ? 'not-allowed' : 'pointer',
            transition: 'background-color 0.2s',
            height: '42px'
          }}
        >
          {searching ? 'Searching...' : 'Search'}
        </button>
      </form>

      {errors.length > 0 && (
        <div style={{ backgroundColor: '#fff5f5', border: '1px solid #feb2b2', borderRadius: 6, padding: '12px 16px', marginBottom: 20, color: '#c53030' }}>
          {errors.map((e, i) => (
            <p key={i} style={{ margin: '4px 0', fontSize: '14px' }}>
              {e.platform ? `[${PLATFORM_LABELS[e.platform] || e.platform}] ${e.message}` : e.message}
            </p>
          ))}
        </div>
      )}

      {job && (
        <div style={{ 
          backgroundColor: '#ebf8ff', 
          border: '1px solid #bee3f8', 
          borderRadius: 8, 
          padding: 20, 
          marginBottom: 24, 
          display: 'flex', 
          flexDirection: 'column', 
          gap: 12 
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontWeight: '600', color: '#2b6cb0', fontSize: '16px' }}>
              {job.status === 'completed' ? '✨ Import finished successfully!' : '⏳ Crawling reviews...'}
            </span>
            <span style={{ fontSize: '14px', color: '#4a5568', fontWeight: '500' }}>
              {job.fetched_count || 0} reviews fetched
            </span>
          </div>
          <div style={{ height: 8, backgroundColor: '#e2e8f0', borderRadius: 4, overflow: 'hidden' }}>
            <div 
              style={{ 
                height: '100%', 
                width: job.status === 'completed' ? '100%' : '60%', 
                backgroundColor: '#3182ce', 
                borderRadius: 4, 
                transition: 'width 0.4s ease-out' 
              }} 
            />
          </div>
          {job.status === 'running' && (
            <div style={{ fontSize: '13px', color: '#718096', fontStyle: 'italic' }}>
              Note: Play Store pagination can take a minute for popular apps. Please do not close this window.
            </div>
          )}
        </div>
      )}

      {results.length > 0 && (
        <div>
          <h3 style={{ margin: '0 0 12px 0', fontSize: '18px', color: '#2d3748' }}>Search Results</h3>
          <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: 12 }}>
            {results.map((r) => (
              <li
                key={`${r.platform}-${r.store_app_id}`}
                style={{ 
                  display: 'flex', 
                  gap: 16, 
                  alignItems: 'center', 
                  border: '1px solid #e2e8f0', 
                  padding: 16, 
                  borderRadius: 8,
                  backgroundColor: '#fff',
                  transition: 'transform 0.15s, box-shadow 0.15s',
                  boxShadow: '0 1px 3px rgba(0,0,0,0.05)'
                }}
              >
                {r.icon_url ? (
                  <img src={r.icon_url} alt={`${r.name} Icon`} style={{ width: 56, height: 56, borderRadius: 12, objectFit: 'cover', border: '1px solid #edf2f7' }} />
                ) : (
                  <div style={{ width: 56, height: 56, borderRadius: 12, backgroundColor: '#e2e8f0', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 'bold', color: '#a0aec0' }}>
                    APP
                  </div>
                )}
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontWeight: '700', fontSize: '16px', color: '#1a202c', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                    {r.name}
                  </div>
                  <div style={{ fontSize: '14px', color: '#718096', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', marginTop: 2 }}>
                    {r.developer || 'Unknown Developer'}
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 4, fontSize: '13px', fontWeight: '500' }}>
                    <span style={{ 
                      padding: '2px 8px', 
                      borderRadius: 12, 
                      fontSize: '11px', 
                      fontWeight: '700',
                      textTransform: 'uppercase',
                      backgroundColor: r.platform === 'playstore' ? '#ebf8ff' : '#f3e8ff',
                      color: r.platform === 'playstore' ? '#2b6cb0' : '#6b46c1'
                    }}>
                      {PLATFORM_LABELS[r.platform] || r.platform}
                    </span>
                    {r.rating != null && (
                      <span style={{ color: '#d69e2e', display: 'flex', alignItems: 'center', gap: 2 }}>
                        ⭐ {r.rating.toFixed(1)}
                      </span>
                    )}
                  </div>
                </div>
                <button 
                  type="button" 
                  onClick={() => handleFetch(r)}
                  style={{ 
                    padding: '8px 16px', 
                    fontSize: '14px', 
                    fontWeight: '600',
                    color: '#3182ce',
                    backgroundColor: '#fff',
                    border: '1px solid #3182ce',
                    borderRadius: 6,
                    cursor: 'pointer',
                    transition: 'all 0.2s',
                    whiteSpace: 'nowrap'
                  }}
                  onMouseOver={(e) => {
                    e.currentTarget.style.backgroundColor = '#ebf8ff';
                  }}
                  onMouseOut={(e) => {
                    e.currentTarget.style.backgroundColor = '#fff';
                  }}
                >
                  Import Reviews
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
