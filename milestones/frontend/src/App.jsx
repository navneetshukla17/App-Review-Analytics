import { Route, Routes, NavLink } from 'react-router-dom';
import DashboardPage from './pages/DashboardPage.jsx';
import SearchPage from './pages/SearchPage.jsx';

export default function App() {
  return (
    <div style={{ fontFamily: 'system-ui, sans-serif', maxWidth: 1100, margin: '0 auto', padding: 24, color: '#2c3e50' }}>
      <header style={{ borderBottom: '1px solid #e2e8f0', paddingBottom: 16, marginBottom: 24, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h2 style={{ margin: 0, color: '#1a365d' }}>📈 Store Reviews Insights</h2>
        <nav style={{ display: 'flex', gap: 16 }}>
          <NavLink 
            to="/" 
            style={({ isActive }) => ({
              textDecoration: 'none',
              color: isActive ? '#3182ce' : '#4a5568',
              fontWeight: isActive ? '600' : '400',
              padding: '6px 12px',
              borderRadius: '4px',
              backgroundColor: isActive ? '#ebf8ff' : 'transparent',
              transition: 'all 0.2s'
            })}
          >
            Search &amp; Fetch
          </NavLink>
          <NavLink 
            to="/dashboard" 
            style={({ isActive }) => ({
              textDecoration: 'none',
              color: isActive ? '#3182ce' : '#4a5568',
              fontWeight: isActive ? '600' : '400',
              padding: '6px 12px',
              borderRadius: '4px',
              backgroundColor: isActive ? '#ebf8ff' : 'transparent',
              transition: 'all 0.2s'
            })}
          >
            Dashboard
          </NavLink>
        </nav>
      </header>
      <main style={{ backgroundColor: '#ffffff', borderRadius: '8px', boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)', padding: 24 }}>
        <Routes>
          <Route path="/" element={<SearchPage />} />
          <Route path="/dashboard" element={<DashboardPage />} />
        </Routes>
      </main>
    </div>
  );
}
