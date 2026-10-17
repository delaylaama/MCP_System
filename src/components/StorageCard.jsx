import React from 'react';
import { ProviderStorageIcon } from './ProviderIcon';
import toast from 'react-hot-toast';

export default function StorageCard({ provider, onConnect, onDisconnect, onExploreLocal, onShowDetails }) {
  const usageColor =
    provider.usedPercent > 80 ? 'var(--color-danger)' : provider.usedPercent > 60 ? 'var(--color-warning)' : 'var(--color-primary)';

  return (
    <div className="card-base storage-card">
      <div className="storage-card-header">
        <ProviderStorageIcon provider={provider.name} />
        <span className={`storage-status-badge ${provider.connected ? 'connected' : 'disconnected'}`}>
          {provider.connected ? (
            <><i className="bi bi-check-circle-fill" /> Connected</>
          ) : (
            <><i className="bi bi-x-circle" /> Not Connected</>
          )}
        </span>
      </div>

      <div style={{ fontSize: 16, fontWeight: 700, color: 'var(--color-text-primary)', marginBottom: 4 }}>
        {provider.name}
      </div>
      <div style={{ fontSize: 13, color: 'var(--color-text-secondary)', marginBottom: 10 }}>
        {provider.connected ? (
          <>
            <i className="bi bi-file-earmark" style={{ marginRight: 5 }} />
            {provider.fileCount} files &nbsp;·&nbsp;
            <i className="bi bi-hdd" style={{ marginRight: 5 }} />
            {provider.usedStorage} of {provider.totalStorage}
          </>
        ) : (
          provider.description
        )}
      </div>

      {provider.connected && (
        <>
          <div className="storage-usage-bar">
            <div
              className="storage-usage-fill"
              style={{ width: `${provider.usedPercent}%`, background: usageColor }}
            />
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11.5, color: 'var(--color-text-muted)' }}>
            <span>{provider.usedPercent}% used</span>
            <span>Synced {provider.lastSync}</span>
          </div>
        </>
      )}

      <div className="storage-card-actions">
        {provider.connected ? (
          <>
            {provider.id === 'local' ? (
              <>
                <button
                  className="btn-outline-custom"
                  style={{ flex: 1, justifyContent: 'center', fontSize: 12.5 }}
                  onClick={() => onShowDetails?.(provider)}
                >
                  <i className="bi bi-info-circle" /> Details
                </button>
                <button
                  className="btn-primary-custom"
                  style={{ flex: 1.2, justifyContent: 'center', fontSize: 12.5 }}
                  onClick={() => onExploreLocal?.()}
                >
                  <i className="bi bi-hdd-network" /> Explore Drives
                </button>
              </>
            ) : (
              <>
                <button
                  className="btn-outline-custom"
                  style={{ flex: 1, justifyContent: 'center', fontSize: 12.5 }}
                  onClick={() => onShowDetails?.(provider)}
                >
                  <i className="bi bi-info-circle" /> Details
                </button>
                <button
                  className="btn-outline-custom"
                  style={{ flex: 1, justifyContent: 'center', fontSize: 12.5, color: 'var(--color-danger)', borderColor: 'var(--color-danger)' }}
                  onClick={() => onDisconnect?.(provider.id)}
                >
                  <i className="bi bi-x-circle" /> Disconnect
                </button>
              </>
            )}
          </>
        ) : (
          <button
            className="btn-primary-custom"
            style={{ flex: 1, justifyContent: 'center', fontSize: 13 }}
            onClick={() => onConnect?.(provider)}
          >
            <i className="bi bi-plug" /> Connect {provider.name}
          </button>
        )}
      </div>
    </div>
  );
}
