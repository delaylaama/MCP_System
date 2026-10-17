import React, { useState } from 'react';
import { useApp } from '../context/AppContext';
import toast from 'react-hot-toast';

function ToggleSwitch({ checked, onChange }) {
  return (
    <label className="toggle-switch">
      <input type="checkbox" checked={checked} onChange={onChange} />
      <span className="toggle-slider" />
    </label>
  );
}

function RadioOption({ name, value, checked, onChange, label, desc }) {
  return (
    <label
      style={{
        display: 'flex',
        alignItems: 'flex-start',
        gap: 10,
        padding: '12px',
        border: `1.5px solid ${checked ? 'var(--color-primary)' : 'var(--color-border)'}`,
        borderRadius: 'var(--radius-md)',
        cursor: 'pointer',
        background: checked ? 'var(--color-primary-light)' : 'transparent',
        transition: 'all 0.15s',
        marginBottom: 8,
      }}
    >
      <input type="radio" name={name} value={value} checked={checked} onChange={onChange} style={{ accentColor: 'var(--color-primary)', marginTop: 2 }} />
      <div>
        <div style={{ fontSize: 13.5, fontWeight: 500, color: checked ? 'var(--color-primary)' : 'var(--color-text-primary)' }}>{label}</div>
        {desc && <div style={{ fontSize: 12, color: 'var(--color-text-muted)', marginTop: 2 }}>{desc}</div>}
      </div>
    </label>
  );
}

export default function Settings() {
  const { user, theme, setTheme, searchMode, setSearchMode } = useApp();
  const [profile, setProfile] = useState({
    name: user?.fullName || user?.name || '',
    email: user?.email || '',
  });
  const [notifications, setNotifications] = useState({ syncAlerts: true, searchSuggestions: true, weeklyDigest: false });
  const [password, setPassword] = useState({ current: '', newPass: '', confirm: '' });

  const handleProfileSave = () => {
    toast.success('Profile updated successfully!');
  };

  const handleSearchModeChange = (mode) => {
    setSearchMode(mode);
    const labels = {
      keyword: 'Text-Based Keyword Search (FTS5)',
      semantic: 'Semantic Vector Search (LanceDB)',
      hybrid_ai: 'Hybrid AI Search (RRF k=60)',
    };
    toast.success(`Search engine set to ${labels[mode] || mode}`);
  };

  const handlePasswordChange = () => {
    if (!password.current) { toast.error('Enter your current password.'); return; }
    if (password.newPass.length < 6) { toast.error('New password must be at least 6 characters.'); return; }
    if (password.newPass !== password.confirm) { toast.error('Passwords do not match.'); return; }
    toast.success('Password changed successfully!');
    setPassword({ current: '', newPass: '', confirm: '' });
  };

  return (
    <div style={{ maxWidth: 720 }}>
      <div className="page-header">
        <h1 className="page-title">Settings</h1>
        <p className="page-subtitle">Manage your profile, preferences, and account settings.</p>
      </div>

      {/* ── Profile ── */}
      <div className="settings-section">
        <div className="settings-section-title">Profile</div>
        <div className="settings-section-desc">Manage your personal information.</div>
        <div className="card-base settings-card">
          {/* Avatar */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginBottom: 24 }}>
            <div style={{ width: 64, height: 64, borderRadius: '50%', background: 'var(--color-primary)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'white', fontSize: 24, fontWeight: 700 }}>
              {profile.name?.charAt(0)?.toUpperCase() || 'U'}
            </div>
            <div>
              <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--color-text-primary)' }}>{profile.name || 'Your Name'}</div>
              <div style={{ fontSize: 12.5, color: 'var(--color-text-muted)', marginBottom: 8 }}>{profile.email}</div>
              <button
                className="btn-outline-custom"
                style={{ fontSize: 12, padding: '5px 12px' }}
                onClick={() => toast('Profile picture upload coming soon!', { icon: '📷' })}
              >
                <i className="bi bi-camera" /> Change Photo
              </button>
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 16 }}>
            <div>
              <label className="form-label-custom" htmlFor="set-name">Full Name</label>
              <input
                id="set-name"
                type="text"
                className="form-control-custom"
                value={profile.name}
                onChange={(e) => setProfile({ ...profile, name: e.target.value })}
              />
            </div>
            <div>
              <label className="form-label-custom" htmlFor="set-email">Email Address</label>
              <input
                id="set-email"
                type="email"
                className="form-control-custom"
                value={profile.email}
                onChange={(e) => setProfile({ ...profile, email: e.target.value })}
              />
            </div>
          </div>

          <button className="btn-primary-custom" onClick={handleProfileSave}>
            <i className="bi bi-check2" /> Save Changes
          </button>
        </div>
      </div>

      {/* ── AI Search ── */}
      <div className="settings-section">
        <div className="settings-section-title">AI Search</div>
        <div className="settings-section-desc">Configure how the AI searches your files.</div>
        <div className="card-base settings-card">
          <div style={{ fontSize: 13.5, fontWeight: 600, color: 'var(--color-text-primary)', marginBottom: 12 }}>Search Mode</div>
          <RadioOption
            name="searchMode"
            value="hybrid_ai"
            checked={searchMode === 'hybrid_ai'}
            onChange={() => handleSearchModeChange('hybrid_ai')}
            label="Hybrid AI Search (Recommended)"
            desc="Combines FTS5 keyword matching + LanceDB semantic text (MiniLM) and visual (CLIP) vectors with Reciprocal Rank Fusion."
          />
          <RadioOption
            name="searchMode"
            value="semantic"
            checked={searchMode === 'semantic'}
            onChange={() => handleSearchModeChange('semantic')}
            label="Semantic Vector Search"
            desc="Uses 100% on-device AI embeddings (MiniLM & CLIP) to match context, concepts, and images even with mismatched keywords."
          />
          <RadioOption
            name="searchMode"
            value="keyword"
            checked={searchMode === 'keyword'}
            onChange={() => handleSearchModeChange('keyword')}
            label="Text-Based Keyword Search (FTS5)"
            desc="Ultra-fast exact and prefix keyword matching across file names, paths, and extracted text snippets via SQLite FTS5."
          />

          <div className="divider" />

          <div style={{ fontSize: 13.5, fontWeight: 600, color: 'var(--color-text-primary)', marginBottom: 12 }}>Notifications</div>
          {[
            { key: 'syncAlerts', label: 'Sync Alerts', desc: 'Get notified when your storage is syncing.' },
            { key: 'searchSuggestions', label: 'Search Suggestions', desc: 'Show AI-powered suggestions while searching.' },
            { key: 'weeklyDigest', label: 'Weekly Digest', desc: 'Receive a weekly summary of your file activity.' },
          ].map((item) => (
            <div key={item.key} className="settings-row">
              <div>
                <div className="settings-row-label">{item.label}</div>
                <div className="settings-row-desc">{item.desc}</div>
              </div>
              <ToggleSwitch
                checked={notifications[item.key]}
                onChange={() => setNotifications((n) => ({ ...n, [item.key]: !n[item.key] }))}
              />
            </div>
          ))}
        </div>
      </div>

      {/* ── Appearance ── */}
      <div className="settings-section">
        <div className="settings-section-title">Appearance</div>
        <div className="settings-section-desc">Customize the look of the application.</div>
        <div className="card-base settings-card">
          <div style={{ fontSize: 13.5, fontWeight: 600, color: 'var(--color-text-primary)', marginBottom: 12 }}>Theme</div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 10 }}>
            {[
              { value: 'light', icon: 'bi-sun', label: 'Light' },
              { value: 'dark', icon: 'bi-moon', label: 'Dark' },
              { value: 'system', icon: 'bi-circle-half', label: 'System' },
            ].map((t) => (
              <button
                key={t.value}
                onClick={() => {
                  const newTheme = t.value === 'system'
                    ? (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light')
                    : t.value;
                  setTheme(newTheme);
                  toast.success(`Theme set to ${t.label}`);
                }}
                style={{
                  padding: '16px 12px',
                  border: `1.5px solid ${theme === t.value || (t.value === 'system') ? 'var(--color-primary)' : 'var(--color-border)'}`,
                  borderRadius: 'var(--radius-md)',
                  background: theme === t.value ? 'var(--color-primary-light)' : 'transparent',
                  cursor: 'pointer',
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  gap: 8,
                  transition: 'all 0.15s',
                  fontFamily: 'var(--font-family)',
                }}
              >
                <i className={`bi ${t.icon}`} style={{ fontSize: 20, color: theme === t.value ? 'var(--color-primary)' : 'var(--color-text-secondary)' }} />
                <span style={{ fontSize: 13, fontWeight: 500, color: theme === t.value ? 'var(--color-primary)' : 'var(--color-text-secondary)' }}>{t.label}</span>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* ── Security ── */}
      <div className="settings-section">
        <div className="settings-section-title">Security</div>
        <div className="settings-section-desc">Manage your account security and connected accounts.</div>
        <div className="card-base settings-card">
          <div style={{ fontSize: 13.5, fontWeight: 600, color: 'var(--color-text-primary)', marginBottom: 16 }}>Change Password</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12, marginBottom: 16 }}>
            <div>
              <label className="form-label-custom" htmlFor="set-curr-pass">Current Password</label>
              <input
                id="set-curr-pass"
                type="password"
                className="form-control-custom"
                placeholder="Enter current password"
                value={password.current}
                onChange={(e) => setPassword({ ...password, current: e.target.value })}
              />
            </div>
            <div>
              <label className="form-label-custom" htmlFor="set-new-pass">New Password</label>
              <input
                id="set-new-pass"
                type="password"
                className="form-control-custom"
                placeholder="At least 6 characters"
                value={password.newPass}
                onChange={(e) => setPassword({ ...password, newPass: e.target.value })}
              />
            </div>
            <div>
              <label className="form-label-custom" htmlFor="set-confirm-pass">Confirm New Password</label>
              <input
                id="set-confirm-pass"
                type="password"
                className="form-control-custom"
                placeholder="Repeat new password"
                value={password.confirm}
                onChange={(e) => setPassword({ ...password, confirm: e.target.value })}
              />
            </div>
          </div>
          <button className="btn-primary-custom" onClick={handlePasswordChange}>
            <i className="bi bi-shield-lock" /> Update Password
          </button>

          <div className="divider" />

          <div style={{ fontSize: 13.5, fontWeight: 600, color: 'var(--color-text-primary)', marginBottom: 12 }}>Connected Accounts</div>
          {[
            { icon: 'bi-google', label: 'Google Drive', status: 'Connected', color: '#4285f4' },
            { icon: 'bi-microsoft', label: 'OneDrive', status: 'Connected', color: '#0078d4' },
            { icon: 'bi-dropbox', label: 'Dropbox', status: 'Connected', color: '#0061ff' },
          ].map((acc) => (
            <div key={acc.label} className="settings-row">
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <i className={`bi ${acc.icon}`} style={{ fontSize: 18, color: acc.color }} />
                <div>
                  <div className="settings-row-label">{acc.label}</div>
                  <div className="settings-row-desc" style={{ color: 'var(--color-success)' }}>{acc.status}</div>
                </div>
              </div>
              <button
                className="btn-outline-custom"
                style={{ fontSize: 12, padding: '5px 12px' }}
                onClick={() => toast(`${acc.label} management coming soon!`, { icon: '⚙️' })}
              >
                Manage
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* Danger zone */}
      <div className="settings-section">
        <div className="settings-section-title" style={{ color: 'var(--color-danger)' }}>Danger Zone</div>
        <div className="settings-section-desc">Irreversible actions. Proceed with caution.</div>
        <div className="card-base settings-card" style={{ borderColor: 'var(--color-danger)' }}>
          <div className="settings-row">
            <div>
              <div className="settings-row-label">Delete All Data</div>
              <div className="settings-row-desc">Removes all your file indexes and preferences. Cannot be undone.</div>
            </div>
            <button
              className="btn-outline-custom"
              style={{ color: 'var(--color-danger)', borderColor: 'var(--color-danger)', fontSize: 12.5 }}
              onClick={() => toast.error('This would delete all data. Action not available in demo.')}
            >
              Delete Data
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
