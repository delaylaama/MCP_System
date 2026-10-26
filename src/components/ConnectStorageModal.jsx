import React, { useState } from 'react';

export default function ConnectStorageModal({ provider, onConfirm, onInstantConfirm, onClose }) {
  const [connectingMode, setConnectingMode] = useState(null);

  if (!provider) return null;

  const permissions = provider.permissions || ['Read files', 'Search files', 'Read file metadata'];

  const handleInstant = async () => {
    setConnectingMode('instant');
    try {
      if (onInstantConfirm) {
        await onInstantConfirm(provider);
      } else {
        await onConfirm?.(provider);
      }
    } finally {
      setConnectingMode(null);
    }
  };

  const handleLive = async () => {
    setConnectingMode('live');
    try {
      await onConfirm?.(provider);
    } finally {
      // If redirection happened, window navigates away; otherwise reset
      setConnectingMode(null);
    }
  };

  return (
    <div className="modal-overlay" onClick={connectingMode ? undefined : onClose}>
      <div className="modal-box" onClick={(e) => e.stopPropagation()} style={{ maxWidth: 520 }}>
        {/* Header */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <div style={{ width: 36, height: 36, borderRadius: '50%', background: 'rgba(59, 130, 246, 0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--color-primary)' }}>
              <i className="bi bi-cloud-arrow-up-fill" style={{ fontSize: 18 }} />
            </div>
            <h3 className="modal-title" style={{ margin: 0 }}>Connect {provider.name}</h3>
          </div>
          <button
            onClick={onClose}
            disabled={!!connectingMode}
            style={{ background: 'none', border: 'none', cursor: connectingMode ? 'not-allowed' : 'pointer', fontSize: 18, color: 'var(--color-text-muted)' }}
          >
            <i className="bi bi-x" />
          </button>
        </div>

        <p className="modal-desc" style={{ marginBottom: 14 }}>
          Connect your {provider.name} storage to index, search, and manage your cloud files through AI semantic search.
        </p>

        {/* Permissions */}
        <div style={{ marginBottom: 6, fontSize: 12.5, fontWeight: 600, color: 'var(--color-text-secondary)' }}>
          Permissions requested:
        </div>
        <div className="modal-permissions" style={{ marginBottom: 14 }}>
          {permissions.map((perm) => (
            <div key={perm} className="modal-permission-item">
              <i className="bi bi-check-circle-fill" />
              <span>{perm}</span>
            </div>
          ))}
        </div>

        <div
          style={{
            padding: '10px 14px',
            background: 'var(--color-warning-light)',
            borderRadius: 'var(--radius-md)',
            fontSize: 12,
            color: 'var(--color-warning)',
            marginBottom: 18,
            display: 'flex',
            gap: 8,
            alignItems: 'center',
          }}
        >
          <i className="bi bi-shield-check" style={{ fontSize: 15 }} />
          <span>We request read permissions only. We never modify, share, or delete your cloud files.</span>
        </div>

        {/* Connection Options */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10, marginBottom: 18 }}>
          <button
            className="btn-primary-custom"
            style={{ width: '100%', justifyContent: 'center', padding: '11px 16px', gap: 8, fontSize: 13.5 }}
            disabled={!!connectingMode}
            onClick={handleInstant}
          >
            {connectingMode === 'instant' ? (
              <>
                <i className="bi bi-arrow-repeat spin" />
                Connecting Sandbox...
              </>
            ) : (
              <>
                <i className="bi bi-lightning-charge-fill" style={{ color: '#f59e0b' }} />
                Instant Sandbox Connect (Recommended)
              </>
            )}
          </button>
          <button
            className="btn-outline-custom"
            style={{ width: '100%', justifyContent: 'center', padding: '10px 16px', gap: 8, fontSize: 13 }}
            disabled={!!connectingMode}
            onClick={handleLive}
          >
            {connectingMode === 'live' ? (
              <>
                <i className="bi bi-arrow-repeat spin" />
                Preparing Cloud Sign-In...
              </>
            ) : (
              <>
                <i className="bi bi-box-arrow-up-right" />
                Live Cloud OAuth Sign-In
              </>
            )}
          </button>
        </div>

        <div style={{ textAlign: 'center' }}>
          <button
            onClick={onClose}
            disabled={!!connectingMode}
            style={{ background: 'none', border: 'none', color: 'var(--color-text-muted)', cursor: connectingMode ? 'not-allowed' : 'pointer', fontSize: 12.5 }}
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
}
