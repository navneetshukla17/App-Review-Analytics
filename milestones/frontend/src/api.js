const API = '/api';

async function request(url, options = {}) {
  const res = await fetch(url, options);
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail || detail;
    } catch {
      /* ignore non-JSON errors */
    }
    throw new Error(detail);
  }
  return res.json();
}

export const searchApps = (q, platform) =>
  request(`${API}/apps/search?q=${encodeURIComponent(q)}&platform=${platform}`);

export const createApp = (candidate) =>
  request(`${API}/apps`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(candidate),
  });

export const listApps = () => request(`${API}/apps`);

export const estimateReviews = (appId) =>
  request(`${API}/apps/${appId}/review-estimate`);

export const getReviews = (appId, params) =>
  request(`${API}/apps/${appId}/reviews?${new URLSearchParams(params)}`);

export const getStats = (appId) => request(`${API}/apps/${appId}/stats`);

export const startFetch = (appId, limit = null) => {
  const params = new URLSearchParams();
  if (limit) params.append('limit', limit);
  return request(`${API}/apps/${appId}/fetch${params.toString() ? '?' + params.toString() : ''}`, { method: 'POST' });
};

export const getJob = (jobId) => request(`${API}/jobs/${jobId}`);

export const exportUrl = (appId, format, params = {}) =>
  `${API}/apps/${appId}/export?format=${format}${Object.keys(params).length ? `&${new URLSearchParams(params)}` : ''}`;
