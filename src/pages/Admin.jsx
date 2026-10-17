import React, { useState, useEffect } from 'react';
import api from '../services/api';
import toast from 'react-hot-toast';

export default function Admin() {
  const [isAdmin, setIsAdmin] = useState(() => !!localStorage.getItem('mcp_admin_token'));
  const [loginForm, setLoginForm] = useState({ username: 'admin', password: '' });
  const [loggingIn, setLoggingIn] = useState(false);

  const [overview, setOverview] = useState(null);
  const [users, setUsers] = useState([]);
  const [indexingStatus, setIndexingStatus] = useState(null);
  const [loadingData, setLoadingData] = useState(false);
  const [reindexing, setReindexing] = useState(false);

  const handleAdminLogin = async (e) => {
    e.preventDefault();
    setLoggingIn(true);
    try {
      const { data } = await api.post('/api/admin/login', loginForm);
      if (data.success) {
        localStorage.setItem('mcp_admin_token', data.token);
        setIsAdmin(true);
        toast.success('Admin authentication verified.');
      }
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Invalid admin credentials.');
    } finally {
      setLoggingIn(false);
    }
  };

  const handleAdminLogout = () => {
    localStorage.removeItem('mcp_admin_token');
    setIsAdmin(false);
    toast('Logged out of admin panel.');
  };

  const fetchAdminData = async () => {
    if (!isAdmin) return;
    setLoadingData(true);
    try {
      const [ovRes, uRes, idxRes] = await Promise.all([
        api.get('/api/admin/overview'),
        api.get('/api/admin/users'),
        api.get('/api/admin/index-status'),
      ]);
      setOverview(ovRes.data);
      setUsers(uRes.data);
      setIndexingStatus(idxRes.data);
    } catch (err) {
      console.warn('Error loading admin data:', err);
    } finally {
      setLoadingData(false);
    }
  };

  useEffect(() => {
    if (isAdmin) {
      fetchAdminData();
      const interval = setInterval(() => {
        api.get('/api/admin/index-status').then((r) => setIndexingStatus(r.data)).catch(() => {});
      }, 5000);
      return () => clearInterval(interval);
    }
  }, [isAdmin]);

  const handleToggleUser = async (userId) => {
    try {
      const { data } = await api.post(`/api/admin/users/${userId}/toggle-status`);
      setUsers((prev) =>
        prev.map((u) => (u.id === userId ? { ...u, is_active: data.is_active } : u))
      );
      toast.success(`User ${data.is_active ? 'activated' : 'disabled'} successfully.`);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to update user status.');
    }
  };

  const handleTriggerReindex = async () => {
    setReindexing(true);
    try {
      await api.post('/api/admin/reindex');
      toast.success('Background incremental index pass triggered.');
      const idxRes = await api.get('/api/admin/index-status');
      setIndexingStatus(idxRes.data);
    } catch (err) {
      toast.error('Failed to trigger re-index.');
    } finally {
      setReindexing(false);
    }
  };

  if (!isAdmin) {
    return (
      <div style={{ maxWidth: 440, margin: '60px auto' }}>
        <div className="card-base" style={{ padding: 32, borderRadius: 16 }}>
          <div style={{ textAlign: 'center', marginBottom: 24 }}>
            <div
              style={{
                width: 56,
                height: 56,
                borderRadius: '50%',
                background: 'rgba(59,130,246,0.1)',
                color: 'var(--color-primary)',
                display: 'inline-flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: 26,
                marginBottom: 12,
              }}
            >
              <i className="bi bi-shield-lock-fill" />
            </div>
            <h2 style={{ fontSize: 20, fontWeight: 700, margin: '0 0 6px', color: 'var(--color-text-primary)' }}>
              Admin Control Center
            </h2>
            <p style={{ fontSize: 13, color: 'var(--color-text-muted)', margin: 0 }}>
              Authenticate with administrative credentials to access active data and system metrics.
            </p>
          </div>

          <form onSubmit={handleAdminLogin}>
            <div style={{ marginBottom: 16 }}>
              <label className="form-label-custom" htmlFor="admin-user">Username</label>
              <input
                id="admin-user"
                type="text"
                className="form-control-custom"
                placeholder="admin"
                value={loginForm.username}
                onChange={(e) => setLoginForm({ ...loginForm, username: e.target.value })}
                required
              />
            </div>

            <div style={{ marginBottom: 24 }}>
              <label className="form-label-custom" htmlFor="admin-pass">Password / Passcode</label>
              <input
                id="admin-pass"
                type="password"
                className="form-control-custom"
                placeholder="Enter admin password"
                value={loginForm.password}
                onChange={(e) => setLoginForm({ ...loginForm, password: e.target.value })}
                required
              />
            </div>

            <button
              type="submit"
              disabled={loggingIn}
              className="btn-primary-custom"
              style={{ width: '100%', justifyContent: 'center', padding: '10px 0', fontSize: 14 }}
            >
              {loggingIn ? 'Authenticating...' : 'Sign In as Administrator'}
            </button>
          </form>
        </div>
      </div>
    );
  }

  const sys = overview?.system || {};
  const metrics = overview?.metrics || {};
  const sources = metrics.sources_breakdown || {};
  const idx = indexingStatus?.status || {};
  const isCurrentlyIndexing = idx.status === 'indexing';

  return (
    <div style={{ maxWidth: 1080 }}>
      {/* Page Header */}
      <div className="page-header">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 14 }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <h1 className="page-title" style={{ margin: 0 }}>Administration & Data Control</h1>
              <span className="badge-connected" style={{ fontSize: 11, padding: '3px 8px' }}>
                <i className="bi bi-shield-check" /> Active Session
              </span>
            </div>
            <p className="page-subtitle" style={{ margin: '4px 0 0' }}>
              Monitor local AI models, LanceDB vector storage, user logins, and indexing pipelines.
            </p>
          </div>

          <div style={{ display: 'flex', gap: 10 }}>
            <button
              onClick={handleTriggerReindex}
              disabled={reindexing || isCurrentlyIndexing}
              className="btn-primary-custom"
              style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13 }}
            >
              <i className={`bi bi-arrow-repeat ${isCurrentlyIndexing ? 'spin' : ''}`} />
              {isCurrentlyIndexing ? 'Indexing Active...' : 'Re-Index All Sources'}
            </button>
            <button
              onClick={handleAdminLogout}
              className="btn-outline-custom"
              style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 13 }}
            >
              <i className="bi bi-box-arrow-right" /> Exit Admin
            </button>
          </div>
        </div>
      </div>

      {/* Indexing Live Status Banner if active */}
      {isCurrentlyIndexing && (
        <div
          className="card-base"
          style={{
            padding: '14px 20px',
            marginBottom: 20,
            background: 'rgba(59,130,246,0.06)',
            borderColor: 'var(--color-primary)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <div className="spinner-border text-primary" role="status" style={{ width: 20, height: 20 }}>
              <span className="visually-hidden">Indexing...</span>
            </div>
            <div>
              <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--color-primary)' }}>
                Local AI Background Indexer is running
              </div>
              <div style={{ fontSize: 12, color: 'var(--color-text-muted)' }}>
                Processing: <strong>{idx.current_file || 'Scanning files...'}</strong> • Scanned: {idx.total_scanned || 0}
              </div>
            </div>
          </div>
          <span style={{ fontSize: 12, color: 'var(--color-text-muted)' }}>
            Search remains responsive on partial results
          </span>
        </div>
      )}

      {/* Top Metrics Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: 16, marginBottom: 24 }}>
        <div className="card-base" style={{ padding: 20 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
            <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--color-text-muted)', textTransform: 'uppercase' }}>
              Indexed Files
            </span>
            <i className="bi bi-files" style={{ fontSize: 20, color: 'var(--color-primary)' }} />
          </div>
          <div style={{ fontSize: 26, fontWeight: 700, color: 'var(--color-text-primary)' }}>
            {metrics.total_indexed_files || 0}
          </div>
          <div style={{ fontSize: 12, color: 'var(--color-text-muted)', marginTop: 4 }}>
            In SQLite metadata & FTS5 index
          </div>
        </div>

        <div className="card-base" style={{ padding: 20 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
            <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--color-text-muted)', textTransform: 'uppercase' }}>
              LanceDB Vectors
            </span>
            <i className="bi bi-cpu" style={{ fontSize: 20, color: '#10b981' }} />
          </div>
          <div style={{ fontSize: 26, fontWeight: 700, color: 'var(--color-text-primary)' }}>
            {(metrics.text_vectors || 0) + (metrics.image_vectors || 0)}
          </div>
          <div style={{ fontSize: 12, color: 'var(--color-text-muted)', marginTop: 4 }}>
            {metrics.text_vectors || 0} text chunks • {metrics.image_vectors || 0} image vectors
          </div>
        </div>

        <div className="card-base" style={{ padding: 20 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
            <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--color-text-muted)', textTransform: 'uppercase' }}>
              Registered Users
            </span>
            <i className="bi bi-people" style={{ fontSize: 20, color: '#f59e0b' }} />
          </div>
          <div style={{ fontSize: 26, fontWeight: 700, color: 'var(--color-text-primary)' }}>
            {metrics.total_users || 0}
          </div>
          <div style={{ fontSize: 12, color: 'var(--color-text-muted)', marginTop: 4 }}>
            {metrics.active_users || 0} active logins
          </div>
        </div>

        <div className="card-base" style={{ padding: 20 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
            <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--color-text-muted)', textTransform: 'uppercase' }}>
              Local AI Pipeline
            </span>
            <i className="bi bi-shield-check" style={{ fontSize: 20, color: '#8b5cf6' }} />
          </div>
          <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--color-success)', marginTop: 4 }}>
            <i className="bi bi-check-circle-fill" /> 100% Offline Active
          </div>
          <div style={{ fontSize: 11.5, color: 'var(--color-text-muted)', marginTop: 4 }}>
            all-MiniLM-L6-v2 + CLIP ViT-B/32
          </div>
        </div>
      </div>

      {/* Storage Sources Breakdown */}
      <div className="card-base" style={{ padding: 20, marginBottom: 24 }}>
        <h3 style={{ margin: '0 0 16px', fontSize: 15, fontWeight: 700, color: 'var(--color-text-primary)' }}>
          Indexed Storage Breakdown by Source
        </h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 14 }}>
          {[
            { key: 'local', name: 'Local Storage', icon: 'bi-hdd-fill', count: sources.local || 0, color: '#3b82f6' },
            { key: 'google_drive', name: 'Google Drive', icon: 'bi-google', count: sources.google_drive || 0, color: '#ea4335' },
            { key: 'onedrive', name: 'OneDrive', icon: 'bi-cloud-fill', count: sources.onedrive || 0, color: '#0078d4' },
            { key: 'dropbox', name: 'Dropbox', icon: 'bi-box-seam', count: sources.dropbox || 0, color: '#0061ff' },
          ].map((s) => (
            <div key={s.key} style={{ padding: 14, borderRadius: 10, background: 'var(--color-surface-2)', border: '1px solid var(--color-border)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
                <i className={`bi ${s.icon}`} style={{ color: s.color, fontSize: 16 }} />
                <span style={{ fontWeight: 600, fontSize: 13, color: 'var(--color-text-primary)' }}>{s.name}</span>
              </div>
              <div style={{ fontSize: 20, fontWeight: 700, color: 'var(--color-text-primary)' }}>
                {s.count} <span style={{ fontSize: 12, fontWeight: 400, color: 'var(--color-text-muted)' }}>files</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* User Management & Active Logins Table */}
      <div className="card-base" style={{ padding: 20, overflow: 'hidden' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <div>
            <h3 style={{ margin: 0, fontSize: 15, fontWeight: 700, color: 'var(--color-text-primary)' }}>
              User Logins & Active Sessions
            </h3>
            <p style={{ margin: '2px 0 0', fontSize: 12, color: 'var(--color-text-muted)' }}>
              View registered users and control account access.
            </p>
          </div>
          <button onClick={fetchAdminData} className="btn-outline-custom" style={{ padding: '4px 10px', fontSize: 12 }}>
            <i className="bi bi-arrow-clockwise" /> Refresh
          </button>
        </div>

        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--color-border)', color: 'var(--color-text-muted)', fontSize: 11.5, textTransform: 'uppercase' }}>
                <th style={{ padding: '8px 12px', textAlign: 'left' }}>User</th>
                <th style={{ padding: '8px 12px', textAlign: 'left' }}>Email</th>
                <th style={{ padding: '8px 12px', textAlign: 'left' }}>Connected Sources</th>
                <th style={{ padding: '8px 12px', textAlign: 'left' }}>Status</th>
                <th style={{ padding: '8px 12px', textAlign: 'right' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {users.length === 0 ? (
                <tr>
                  <td colSpan={5} style={{ padding: '24px 0', textAlign: 'center', color: 'var(--color-text-muted)' }}>
                    No registered user accounts found.
                  </td>
                </tr>
              ) : (
                users.map((u) => (
                  <tr key={u.id} style={{ borderBottom: '1px solid var(--color-border)' }}>
                    <td style={{ padding: '12px 12px' }}>
                      <div style={{ fontWeight: 600, color: 'var(--color-text-primary)' }}>{u.username}</div>
                      {u.full_name && <div style={{ fontSize: 11.5, color: 'var(--color-text-muted)' }}>{u.full_name}</div>}
                    </td>
                    <td style={{ padding: '12px 12px', color: 'var(--color-text-secondary)' }}>
                      {u.email}
                    </td>
                    <td style={{ padding: '12px 12px' }}>
                      <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                        {u.connected_providers && u.connected_providers.length > 0 ? (
                          u.connected_providers.map((p) => (
                            <span key={p} style={{ fontSize: 11, padding: '2px 6px', borderRadius: 4, background: 'var(--color-surface-2)', border: '1px solid var(--color-border)' }}>
                              {p}
                            </span>
                          ))
                        ) : (
                          <span style={{ fontSize: 12, color: 'var(--color-text-muted)' }}>None</span>
                        )}
                      </div>
                    </td>
                    <td style={{ padding: '12px 12px' }}>
                      <span className={u.is_active ? 'badge-connected' : 'storage-status-badge disconnected'} style={{ fontSize: 11, padding: '2px 8px' }}>
                        {u.is_active ? 'Active' : 'Disabled'}
                      </span>
                    </td>
                    <td style={{ padding: '12px 12px', textAlign: 'right' }}>
                      <button
                        onClick={() => handleToggleUser(u.id)}
                        className="btn-outline-custom"
                        style={{
                          padding: '3px 10px',
                          fontSize: 12,
                          color: u.is_active ? 'var(--color-danger)' : 'var(--color-success)',
                          borderColor: u.is_active ? 'var(--color-danger)' : 'var(--color-success)',
                        }}
                      >
                        {u.is_active ? 'Disable Access' : 'Activate'}
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
