import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useApp } from '../context/AppContext';
import toast from 'react-hot-toast';

export default function Navbar() {
  const { user, logout, theme, setTheme, sidebarOpen, setSidebarOpen } = useApp();
  const navigate = useNavigate();
  const [searchVal, setSearchVal] = useState('');
  const [showDropdown, setShowDropdown] = useState(false);

  const initial = user?.name?.charAt(0)?.toUpperCase() || 'U';

  const handleSearch = (e) => {
    e.preventDefault();
    if (searchVal.trim()) {
      navigate(`/ai-search?q=${encodeURIComponent(searchVal.trim())}`);
      setSearchVal('');
    }
  };

  const handleLogout = () => {
    logout();
    toast.success('Logged out successfully');
    navigate('/login');
    setShowDropdown(false);
  };

  const toggleTheme = () => {
    setTheme((t) => (t === 'dark' ? 'light' : 'dark'));
    toast.success(theme === 'dark' ? 'Switched to light mode' : 'Switched to dark mode');
  };

  return (
    <header className="app-navbar">
      {/* Mobile menu toggle */}
      <button
        className="navbar-toggle-btn"
        onClick={() => setSidebarOpen((o) => !o)}
        title="Toggle sidebar"
      >
        <i className={`bi ${sidebarOpen ? 'bi-x' : 'bi-list'}`} />
      </button>

      {/* Search bar */}
      <div className="navbar-search-wrap">
        <form onSubmit={handleSearch}>
          <div className="navbar-search">
            <i className="bi bi-search" style={{ color: 'var(--color-text-muted)', fontSize: 14 }} />
            <input
              type="text"
              placeholder="Search files with AI... (press Enter)"
              value={searchVal}
              onChange={(e) => setSearchVal(e.target.value)}
            />
            <i className="bi bi-stars" style={{ color: 'var(--color-primary)', fontSize: 14 }} />
          </div>
        </form>
      </div>

      {/* Actions */}
      <div className="navbar-actions">
        {/* Theme toggle */}
        <button className="navbar-icon-btn" onClick={toggleTheme} title="Toggle theme">
          <i className={`bi ${theme === 'dark' ? 'bi-sun' : 'bi-moon'}`} />
        </button>

        {/* Notifications (mock) */}
        <button
          className="navbar-icon-btn"
          onClick={() => toast('No new notifications', { icon: '🔔' })}
          title="Notifications"
        >
          <i className="bi bi-bell" />
        </button>

        {/* Avatar dropdown */}
        <div style={{ position: 'relative' }}>
          <div
            className="navbar-avatar"
            onClick={() => setShowDropdown((v) => !v)}
            title="Profile"
          >
            {initial}
          </div>
          {showDropdown && (
            <div
              style={{
                position: 'absolute',
                right: 0,
                top: '44px',
                background: 'var(--color-surface)',
                border: '1px solid var(--color-border)',
                borderRadius: 'var(--radius-lg)',
                boxShadow: 'var(--shadow-lg)',
                minWidth: 200,
                padding: '8px',
                zIndex: 500,
              }}
            >
              <div style={{ padding: '10px 12px 12px', borderBottom: '1px solid var(--color-border-light)', marginBottom: 6 }}>
                <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--color-text-primary)' }}>
                  {user?.fullName || user?.name}
                </div>
                <div style={{ fontSize: 11.5, color: 'var(--color-text-muted)' }}>{user?.email}</div>
              </div>
              <button
                style={{ width: '100%', textAlign: 'left', background: 'none', border: 'none', padding: '8px 12px', borderRadius: 'var(--radius-md)', fontSize: 13, cursor: 'pointer', color: 'var(--color-text-secondary)', display: 'flex', alignItems: 'center', gap: 8 }}
                onClick={() => { navigate('/settings'); setShowDropdown(false); }}
              >
                <i className="bi bi-person-circle" /> Profile & Settings
              </button>
              <button
                style={{ width: '100%', textAlign: 'left', background: 'none', border: 'none', padding: '8px 12px', borderRadius: 'var(--radius-md)', fontSize: 13, cursor: 'pointer', color: 'var(--color-danger)', display: 'flex', alignItems: 'center', gap: 8 }}
                onClick={handleLogout}
              >
                <i className="bi bi-box-arrow-right" /> Log Out
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
