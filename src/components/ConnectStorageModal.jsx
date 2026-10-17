import React from 'react';

export default function ConnectStorageModal({ provider, onConfirm, onClose }) {
  if (!provider) return null;

  const permissions = provider.permissions || ['Read files', 'Search files', 'Read file metadata'];

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-box" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
          <h3 className="modal-title">Connect {provider.name}</h3>
          <button
            onClick={onClose}
            style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: 18, color: 'var(--color-text-muted)' }}
          >
            <i className="bi bi-x" />
          </button>
        </div>

        <p className="modal-desc">
          Connect your {provider.name} account to search and manage your files through the AI assistant.
        </p>

        {/* Permissions */}
        <div style={{ marginBottom: 6, fontSize: 13, fontWeight: 600, color: 'var(--color-text-secondary)' }}>
          Permissions requested:
        </div>
        <div className="modal-permissions">
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
            fontSize: 12.5,
            color: 'var(--color-warning)',
            marginBottom: 20,
            display: 'flex',
            gap: 8,
            alignItems: 'center',
          }}
        >
          <i className="bi bi-shield-check" />
          We only request read permissions. We never modify or delete your files.
        </div>

        {/* Actions */}
        <div className="modal-actions">
          <button className="btn-outline-custom" onClick={onClose}>
            Cancel
          </button>
          <button className="btn-primary-custom" onClick={() => onConfirm?.(provider)}>
            <i className="bi bi-plug" /> Connect {provider.name}
          </button>
        </div>
      </div>
    </div>
  );
}
