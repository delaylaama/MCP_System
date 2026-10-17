import React, { useState, useEffect } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { useApp } from '../context/AppContext';
import { checkHealth } from '../services/providerService';
import toast from 'react-hot-toast';

const navItems = [
  { to: '/dashboard', icon: 'bi-grid-1x2', label: 'Dashboard' },
  { to: '/ai-search', icon: 'bi-stars', label: 'AI Search' },
  { to: '/files', icon: 'bi-folder2-open', label: 'My Files' },
  { to: '/storage', icon: 'bi-cloud-arrow-up', label: 'Storage' },
  { to: '/recent', icon: 'bi-clock-history', label: 'Recent' },
  { to: '/favorites', icon: 'bi-star', label: 'Favorites' },
  { to: '/settings', icon: 'bi-gear', label: 'Settings' },
  { to: '/admin', icon: 'bi-shield-lock', label: 'Admin Panel' },
];

export default function Sidebar() {
  const { user, logout, sidebarOpen, setSidebarOpen } = useApp();
  const navigate = useNavigate();
  const [mcpStatus, setMcpStatus] = useState('checking');

  useEffect(() => {
    let isMounted = true;
    checkHealth().then((health) => {
      if (isMounted) {
        const isOnline =
          health?.status === 'healthy' ||
          health?.status === 'ok' ||
          health?.mcp_server?.status === 'connected';
        setMcpStatus(isOnline ? 'online' : 'offline');
      }
    });
    return () => { isMounted = false; };
  }, []);

  const handleLogout = () => {
    logout();
    toast.success('Logged out successfully');
    navigate('/login');
  };

  const handleNavClick = () => {
    // Close sidebar on mobile after navigation
    if (window.innerWidth <= 992) {
      setSidebarOpen(false);
    }
  };

  const initial = user?.name?.charAt(0)?.toUpperCase() || 'U';

  return (
    <>
      {/* Mobile overlay */}
      <div
        className={`sidebar-overlay ${sidebarOpen ? 'show' : ''}`}
        onClick={() => setSidebarOpen(false)}
      />

      <aside className={`sidebar ${sidebarOpen ? 'open' : ''}`}>
        {/* Brand */}
        <div className="sidebar-brand">
          <div className="sidebar-brand-icon">
            <i className="bi bi-cpu" />
          </div>
          <div>
            <div className="sidebar-brand-text">AI File Manager</div>
            <div className="sidebar-brand-sub">Universal MCP Platform</div>
          </div>
        </div>

        {/* Navigation */}
        <nav className="sidebar-nav">
          <div className="sidebar-section-label">Main</div>
          {navItems.slice(0, 4).map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `sidebar-nav-item${isActive ? ' active' : ''}`
              }
              onClick={handleNavClick}
            >
              <i className={`bi ${item.icon}`} />
              {item.label}
            </NavLink>
          ))}

          <div className="sidebar-section-label" style={{ marginTop: 8 }}>Library</div>
          {navItems.slice(4, 6).map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `sidebar-nav-item${isActive ? ' active' : ''}`
              }
              onClick={handleNavClick}
            >
              <i className={`bi ${item.icon}`} />
              {item.label}
            </NavLink>
          ))}

          <div className="sidebar-section-label" style={{ marginTop: 8 }}>Account</div>
          {navItems.slice(6).map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `sidebar-nav-item${isActive ? ' active' : ''}`
              }
              onClick={handleNavClick}
            >
              <i className={`bi ${item.icon}`} />
              {item.label}
            </NavLink>
          ))}

          <button
            className="sidebar-nav-item"
            style={{ width: '100%', border: 'none', background: 'none', textAlign: 'left', color: 'var(--color-danger)', marginTop: 4 }}
            onClick={handleLogout}
          >
            <i className="bi bi-box-arrow-right" />
            Log Out
          </button>
        </nav>

        {/* Footer user & status */}
        <div className="sidebar-footer">
          <div
            style={{
              padding: '6px 10px',
              marginBottom: 8,
              borderRadius: 'var(--radius-sm)',
              background: 'var(--color-surface-2)',
              fontSize: 11,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
            }}
          >
            <span style={{ color: 'var(--color-text-muted)' }}>MCP Bridge</span>
            <span style={{ display: 'flex', alignItems: 'center', gap: 5, fontWeight: 600, color: mcpStatus === 'online' ? 'var(--color-success)' : '#f59e0b' }}>
              <span
                style={{
                  width: 7,
                  height: 7,
                  borderRadius: '50%',
                  background: mcpStatus === 'online' ? 'var(--color-success)' : '#f59e0b',
                  display: 'inline-block',
                }}
              />
              {mcpStatus === 'online' ? 'Connected' : 'Offline / Mock'}
            </span>
          </div>
          <div className="sidebar-user" onClick={() => navigate('/settings')}>
            <div className="sidebar-avatar">{initial}</div>
            <div className="sidebar-user-info">
              <div className="sidebar-user-name">{user?.fullName || user?.name || 'User'}</div>
              <div className="sidebar-user-email">{user?.email || ''}</div>
            </div>
          </div>
        </div>
      </aside>
    </>
  );
}
