import { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import * as api from '../api.js';

const PLATFORM_LABELS = { playstore: 'Google Play Store', appstore: 'App Store' };

function FetchReviewsModal({ candidate, onClose, onFetch }) {
  const [estimate, setEstimate] = useState(null);
  const [selectedLimit, setSelectedLimit] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  async function loadEstimate() {
    try {
      // First create the app
      const app = await api.createApp(candidate);
      // Then get estimate
      const data = await api.estimateReviews(app.id);
      setEstimate(data);
      setSelectedLimit(data.suggestions[0]?.value || null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: 'rgba(0,0,0,0.5)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 1000,
      animation: 'fadeIn 0.2s ease-out'
    }}>
      <style>{`
        @keyframes fadeIn {
          from { opacity: 0; }
          to { opacity: 1; }
        }
        @keyframes slideIn {
          from { opacity: 0; transform: translateY(-20px); }
          to { opacity: 1; transform: translateY(0); }
        }
      `}</style>

      {!loading && !estimate && !error && loadEstimate()}

      <div style={{
        backgroundColor: '#fff',
        borderRadius: 12,
        padding: 32,
        maxWidth: '500px',
        width: '90%',
        boxShadow: '0 20px 60px rgba(0,0,0,0.3)',
        animation: 'slideIn 0.3s ease-out'
      }}>
        <h2 style={{ margin: '0 0 8px 0', fontSize: '22px', color: '#1a202c' }}>
          Fetch Reviews
        </h2>
        <p style={{ margin: '0 0 24px 0', fontSize: '14px', color: '#718096' }}>
          {candidate.name}
        </p>

        {error && (
          <div style={{
            backgroundColor: '#fff5f5',
            border: '1px solid #feb2b2',
            borderRadius: 6,
            padding: 12,
            marginBottom: 16,
            color: '#c53030',
            fontSize: '14px'
          }}>
            {error}
          </div>
        )}

        {loading && (
          <div style={{ textAlign: 'center', padding: '20px 0' }}>
            <div style={{
              width: 20,
              height: 20,
              border: '3px solid #e2e8f0',
              borderTop: '3px solid #3182ce',
              borderRadius: '50%',
              animation: 'spin 1s linear infinite',
              margin: '0 auto 12px'
            }} />
            <p style={{ color: '#718096', margin: 0 }}>Analyzing app...</p>
          </div>
        )}

        {estimate && (
          <>
            <div style={{
              backgroundColor: '#f7fafc',
              border: '1px solid #e2e8f0',
              borderRadius: 8,
              padding: 16,
              marginBottom: 24
            }}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
                <div>
                  <p style={{ margin: '0 0 4px 0', fontSize: '12px', color: '#718096', textTransform: 'uppercase' }}>
                    Available
                  </p>
                  <p style={{ margin: 0, fontSize: '20px', fontWeight: '700', color: '#1a202c' }}>
                    {estimate.total_available.toLocaleString()}
                  </p>
                </div>
                <div>
                  <p style={{ margin: '0 0 4px 0', fontSize: '12px', color: '#718096', textTransform: 'uppercase' }}>
                    Already Fetched
                  </p>
                  <p style={{ margin: 0, fontSize: '20px', fontWeight: '700', color: '#48bb78' }}>
                    {estimate.already_fetched.toLocaleString()}
                  </p>
                </div>
              </div>
              <div style={{ marginTop: 12, paddingTop: 12, borderTop: '1px solid #cbd5e0' }}>
                <p style={{ margin: '0 0 4px 0', fontSize: '12px', color: '#718096', textTransform: 'uppercase' }}>
                  Remaining
                </p>
                <p style={{ margin: 0, fontSize: '18px', fontWeight: '700', color: '#3182ce' }}>
                  {estimate.remaining.toLocaleString()}
                </p>
              </div>
            </div>

            <div>
              <label style={{ fontSize: '14px', fontWeight: '600', color: '#4a5568', display: 'block', marginBottom: 8 }}>
                Fetch How Many?
              </label>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 8, marginBottom: 16 }}>
                {estimate.suggestions.map((s) => (
                  <button
                    key={s.value}
                    onClick={() => setSelectedLimit(s.value)}
                    style={{
                      padding: '10px 12px',
                      fontSize: '14px',
                      fontWeight: '600',
                      border: '2px solid',
                      borderRadius: 6,
                      cursor: 'pointer',
                      transition: 'all 0.2s',
                      backgroundColor: selectedLimit === s.value ? '#3182ce' : '#fff',
                      borderColor: selectedLimit === s.value ? '#3182ce' : '#cbd5e0',
                      color: selectedLimit === s.value ? '#fff' : '#2d3748'
                    }}
                  >
                    {s.label}
                  </button>
                ))}
              </div>

              <div style={{
                backgroundColor: '#ebf8ff',
                border: '1px solid #bee3f8',
                borderRadius: 6,
                padding: 12,
                marginBottom: 20,
                fontSize: '13px',
                color: '#2b6cb0'
              }}>
                📊 <strong>Estimated:</strong> {estimate.estimated_cycles} fetching cycle{estimate.estimated_cycles !== 1 ? 's' : ''} needed to get all remaining reviews
              </div>
            </div>

            <div style={{ display: 'flex', gap: 12 }}>
              <button
                onClick={onClose}
                style={{
                  flex: 1,
                  padding: '12px 16px',
                  fontSize: '14px',
                  fontWeight: '600',
                  border: '1px solid #cbd5e0',
                  backgroundColor: '#f7fafc',
                  color: '#4a5568',
                  borderRadius: 6,
                  cursor: 'pointer',
                  transition: 'all 0.2s'
                }}
              >
                Cancel
              </button>
              <button
                onClick={() => onFetch(selectedLimit)}
                style={{
                  flex: 1,
                  padding: '12px 16px',
                  fontSize: '14px',
                  fontWeight: '600',
                  border: 'none',
                  backgroundColor: '#3182ce',
                  color: '#fff',
                  borderRadius: 6,
                  cursor: 'pointer',
                  transition: 'all 0.2s'
                }}
              >
                Start Fetching
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

export default function SearchPage() {
  const [query, setQuery] = useState('');
  const [platform, setPlatform] = useState('both');
  const [reviewLimit, setReviewLimit] = useState(null);
  const [results, setResults] = useState([]);
  const [errors, setErrors] = useState([]);
  const [searching, setSearching] = useState(false);
  const [job, setJob] = useState(null);
  const [fetchModalCandidate, setFetchModalCandidate] = useState(null);
  const navigate = useNavigate();
  const searchTimeoutRef = useRef(null);

  async function performSearch(searchQuery, searchPlatform) {
    if (!searchQuery.trim()) {
      setResults([]);
      setErrors([]);
      return;
    }
    setSearching(true);
    setErrors([]);
    try {
      const data = await api.searchApps(searchQuery.trim(), searchPlatform);
      setResults(data.results);
      setErrors(data.errors || []);
    } catch (err) {
      setErrors([{ message: err.message }]);
      setResults([]);
    } finally {
      setSearching(false);
    }
  }

  function handleQueryChange(e) {
    const newQuery = e.target.value;
    setQuery(newQuery);
    
    // Clear previous timeout
    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current);
    }
    
    // Debounce search - wait 300ms after user stops typing
    searchTimeoutRef.current = setTimeout(() => {
      performSearch(newQuery, platform);
    }, 300);
  }

  function handlePlatformChange(e) {
    const newPlatform = e.target.value;
    setPlatform(newPlatform);
    // Re-search with new platform immediately if there's a query
    if (query.trim()) {
      performSearch(query, newPlatform);
    }
  }

  async function handleSearch(event) {
    event.preventDefault();
    performSearch(query, platform);
  }

  async function handleFetch(candidate, selectedLimit) {
    setFetchModalCandidate(null);
    setJob({ status: 'starting', fetched_count: 0 });
    setErrors([]);
    try {
      const app = await api.createApp(candidate);
      const created = await api.startFetch(app.id, selectedLimit);
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
          alignItems: 'flex-start',
          marginBottom: 24
        }}
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: 6, flex: '1 1 300px' }}>
          <label htmlFor="app-name-input" style={{ fontSize: '14px', fontWeight: '600', color: '#4a5568' }}>App Name</label>
          <input
            id="app-name-input"
            value={query}
            onChange={handleQueryChange}
            placeholder="e.g. Spotify, Instagram, WhatsApp"
            autoComplete="off"
            style={{ 
              padding: '10px 14px', 
              fontSize: '15px', 
              borderRadius: 6, 
              border: '1px solid #cbd5e0',
              outline: 'none',
              transition: 'border-color 0.2s'
            }}
          />
          <p style={{ margin: '4px 0 0 0', fontSize: '12px', color: '#718096', fontStyle: 'italic' }}>
            Results update as you type
          </p>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 6, minWidth: '180px' }}>
          <label htmlFor="platform-select" style={{ fontSize: '14px', fontWeight: '600', color: '#4a5568' }}>Platform</label>
          <select 
            id="platform-select"
            value={platform} 
            onChange={handlePlatformChange} 
            style={{ 
              padding: '10px 14px', 
              fontSize: '15px', 
              borderRadius: 6, 
              border: '1px solid #cbd5e0',
              backgroundColor: '#fff',
              outline: 'none',
              minHeight: '42px'
            }}
          >
            <option value="both">Both Stores</option>
            <option value="playstore">Play Store Only</option>
            <option value="appstore">App Store Only</option>
          </select>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 6, minWidth: '180px' }}>
          <label htmlFor="limit-input" style={{ fontSize: '14px', fontWeight: '600', color: '#4a5568' }}>Review Limit</label>
          <input
            id="limit-input"
            type="number"
            value={reviewLimit || ''}
            onChange={(e) => setReviewLimit(e.target.value ? parseInt(e.target.value) : null)}
            placeholder="No limit"
            style={{ 
              padding: '10px 14px', 
              fontSize: '15px', 
              borderRadius: 6, 
              border: '1px solid #cbd5e0',
              outline: 'none',
              minHeight: '42px'
            }}
          />
          <p style={{ margin: '2px 0 0 0', fontSize: '11px', color: '#718096' }}>
            {reviewLimit ? `Fetch up to ${reviewLimit.toLocaleString()}` : 'Leave empty for all'}
          </p>
        </div>
        <button 
          type="submit" 
          disabled={searching || !query.trim()}
          style={{ 
            padding: '10px 24px', 
            fontSize: '15px', 
            fontWeight: '600',
            color: '#fff',
            backgroundColor: (searching || !query.trim()) ? '#a0aec0' : '#3182ce',
            border: 'none',
            borderRadius: 6,
            cursor: (searching || !query.trim()) ? 'not-allowed' : 'pointer',
            transition: 'background-color 0.2s',
            height: '42px',
            marginTop: '24px'
          }}
        >
          {searching ? 'Searching...' : 'Search'}
        </button>
      </form>

      {searching && query.trim() && (
        <div style={{ 
          display: 'flex', 
          alignItems: 'center', 
          gap: 12,
          padding: 16, 
          backgroundColor: '#ebf8ff', 
          border: '1px solid #bee3f8', 
          borderRadius: 6, 
          marginBottom: 20,
          animation: 'fadeIn 0.3s ease-in'
        }}>
          <div style={{
            width: 20,
            height: 20,
            border: '3px solid #e2e8f0',
            borderTop: '3px solid #3182ce',
            borderRadius: '50%',
            animation: 'spin 1s linear infinite'
          }} />
          <span style={{ color: '#2b6cb0', fontWeight: '500', fontSize: '14px' }}>
            Searching for "{query}"...
          </span>
        </div>
      )}

      <style>{`
        @keyframes fadeIn {
          from {
            opacity: 0;
            transform: translateY(-8px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        @keyframes spin {
          to {
            transform: rotate(360deg);
          }
        }
        @keyframes slideIn {
          from {
            opacity: 0;
            transform: translateY(8px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
      `}</style>

      {errors.length > 0 && (
        <div style={{ 
          backgroundColor: '#fff5f5', 
          border: '1px solid #feb2b2', 
          borderRadius: 6, 
          padding: '12px 16px', 
          marginBottom: 20, 
          color: '#c53030',
          animation: 'fadeIn 0.3s ease-in'
        }}>
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
        <div style={{ animation: 'fadeIn 0.3s ease-in' }}>
          <h3 style={{ margin: '0 0 12px 0', fontSize: '18px', color: '#2d3748' }}>
            Search Results
            <span style={{ fontSize: '14px', color: '#718096', fontWeight: '400', marginLeft: 8 }}>
              ({results.length} result{results.length !== 1 ? 's' : ''} found)
            </span>
          </h3>
          <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: 12 }}>
            {results.map((r, idx) => (
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
                  boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
                  animation: `slideIn 0.4s ease-out ${idx * 50}ms backwards`
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
                  onClick={() => setFetchModalCandidate(r)}
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
                  Fetch reviews
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}

      {fetchModalCandidate && (
        <FetchReviewsModal
          candidate={fetchModalCandidate}
          onClose={() => setFetchModalCandidate(null)}
          onFetch={(limit) => handleFetch(fetchModalCandidate, limit)}
        />
      )}
    </div>
  );
}
