import React, { useEffect, useState } from 'react';
import { listProviders, connectProvider, disconnectProvider, getLocalDrives } from '../services/providerService';
import StorageCard from '../components/StorageCard';
import ConnectStorageModal from '../components/ConnectStorageModal';
import LocalDriveExplorerModal from '../components/LocalDriveExplorerModal';
import DriveFilesModal from '../components/DriveFilesModal';
import LoadingSpinner from '../components/LoadingSpinner';
import toast from 'react-hot-toast';
import { mockStorageProviders } from '../data/mockData';

export default function Storage() {
  const [providers, setProviders] = useState(mockStorageProviders);
  const [systemDrives, setSystemDrives] = useState([]);
  const [loading, setLoading] = useState(false);
  const [connectModal, setConnectModal] = useState(null);
  const [exploreLocalModal, setExploreLocalModal] = useState(false);
  const [detailsModalProvider, setDetailsModalProvider] = useState(null);

  useEffect(() => {
    let isMounted = true;
    Promise.all([listProviders(), getLocalDrives()])
      .then(([provData, drivesData]) => {
        if (!isMounted) return;
        if (provData && provData.length > 0) setProviders(provData);
        if (drivesData && drivesData.length > 0) setSystemDrives(drivesData);
      })
      .catch((err) => {
        console.warn('Error loading storage providers:', err);
      });
    return () => { isMounted = false; };
  }, []);

  const handleConnect = (provider) => {
    setConnectModal(provider);
  };

  const handleConfirmConnect = async (provider) => {
    try {
      if (provider.id === 'local') {
        setProviders((prev) =>
          prev.map((p) => (p.id === provider.id ? { ...p, connected: true } : p))
        );
        toast.success(`${provider.name} connected successfully!`);
      } else {
        const res = await connectProvider(provider.id);
        if (res?.authorization_url) {
          window.location.href = res.authorization_url;
          return;
        } else {
          setProviders((prev) =>
            prev.map((p) => (p.id === provider.id ? { ...p, connected: true } : p))
          );
          toast.success(`${provider.name} connected successfully!`);
        }
      }
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to initiate connection.');
    } finally {
      setConnectModal(null);
    }
  };

  const handleDisconnect = async (providerId) => {
    try {
      await disconnectProvider(providerId);
    } catch {
      // Offline fallback
    }
    setProviders((prev) =>
      prev.map((p) => (p.id === providerId ? { ...p, connected: false } : p))
    );
    const provider = providers.find((p) => p.id === providerId);
    toast.success(`${provider?.name || providerId} disconnected.`);
  };

  if (loading) return <LoadingSpinner message="Loading storage providers..." />;

  const connectedCount = providers.filter((p) => p.connected).length;
  const totalFiles = providers
    .filter((p) => p.connected)
    .reduce((acc, p) => acc + (typeof p.fileCount === 'number' ? p.fileCount : 0), 0);

  return (
    <div>
      <div className="page-header">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 12 }}>
          <div>
            <h1 className="page-title">Connected Storage</h1>
            <p className="page-subtitle">Manage your cloud and local storage connections across all drives.</p>
          </div>
          <button
            className="btn-primary-custom"
            style={{ display: 'flex', alignItems: 'center', gap: 8 }}
            onClick={() => setExploreLocalModal(true)}
          >
            <i className="bi bi-hdd-network" /> Browse Local Drives ({systemDrives.length})
          </button>
        </div>
      </div>

      {/* Summary row */}
      <div style={{ display: 'flex', gap: 16, marginBottom: 24, flexWrap: 'wrap' }}>
        {[
          { icon: 'bi-plug', label: 'Connected Providers', value: `${connectedCount} / ${providers.length}`, color: 'var(--color-primary)', bg: 'var(--color-primary-light)' },
          { icon: 'bi-hdd-stack', label: 'Detected System Disks', value: `${systemDrives.length} Drives (${systemDrives.map((d) => d.drive).join(', ')})`, color: '#0284c7', bg: 'rgba(2,132,199,0.1)' },
          { icon: 'bi-files', label: 'Total Files Indexed', value: totalFiles, color: 'var(--color-success)', bg: 'var(--color-success-light)' },
          { icon: 'bi-shield-check', label: 'Security & Access', value: 'Sandboxed Read-only', color: '#7c3aed', bg: 'rgba(124,58,237,0.1)' },
        ].map((item) => (
          <div key={item.label} className="card-base" style={{ padding: '16px 20px', display: 'flex', alignItems: 'center', gap: 14, flex: '1 1 200px' }}>
            <div style={{ width: 40, height: 40, borderRadius: 'var(--radius-md)', background: item.bg, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <i className={`bi ${item.icon}`} style={{ fontSize: 18, color: item.color }} />
            </div>
            <div>
              <div style={{ fontSize: 16, fontWeight: 700, color: 'var(--color-text-primary)' }}>{item.value}</div>
              <div style={{ fontSize: 12, color: 'var(--color-text-secondary)' }}>{item.label}</div>
            </div>
          </div>
        ))}
      </div>

      {/* System Drives Card Banner */}
      {systemDrives.length > 0 && (
        <div className="card-base" style={{ padding: '20px 24px', marginBottom: 28 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16, flexWrap: 'wrap', gap: 10 }}>
            <div>
              <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--color-text-primary)', display: 'flex', alignItems: 'center', gap: 8 }}>
                <i className="bi bi-pc-display-horizontal text-primary" /> System Drives & Partitions
              </div>
              <div style={{ fontSize: 12.5, color: 'var(--color-text-muted)' }}>
                Direct access to host system storage drives and project file directories.
              </div>
            </div>
            <button
              className="btn-outline-custom"
              style={{ fontSize: 12.5, padding: '6px 12px' }}
              onClick={() => setExploreLocalModal(true)}
            >
              <i className="bi bi-folder2-open" style={{ marginRight: 6 }} /> Open Drive Explorer
            </button>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: 14 }}>
            {systemDrives.map((d) => (
              <div
                key={d.drive}
                onClick={() => setExploreLocalModal(true)}
                style={{
                  background: 'var(--color-surface-2)',
                  border: '1px solid var(--color-border)',
                  borderRadius: 'var(--radius-md)',
                  padding: '14px 16px',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease',
                }}
                onMouseEnter={(e) => { e.currentTarget.style.borderColor = 'var(--color-primary)'; }}
                onMouseLeave={(e) => { e.currentTarget.style.borderColor = 'var(--color-border)'; }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <i className="bi bi-hdd-fill" style={{ color: d.is_system ? '#0284c7' : 'var(--color-text-secondary)', fontSize: 18 }} />
                    <span style={{ fontWeight: 700, fontSize: 13.5, color: 'var(--color-text-primary)' }}>
                      {d.display_name}
                    </span>
                  </div>
                  <span style={{ fontSize: 11, padding: '2px 6px', borderRadius: 4, background: 'var(--color-surface)', color: 'var(--color-text-muted)' }}>
                    {d.file_system}
                  </span>
                </div>

                <div className="storage-usage-bar" style={{ height: 6, margin: '8px 0 6px' }}>
                  <div
                    className="storage-usage-fill"
                    style={{
                      width: `${d.used_percent}%`,
                      background: d.used_percent > 85 ? 'var(--color-danger)' : d.used_percent > 70 ? 'var(--color-warning)' : 'var(--color-primary)',
                    }}
                  />
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11.5, color: 'var(--color-text-muted)' }}>
                  <span>{d.free_formatted} free</span>
                  <span>{d.used_percent}% of {d.total_formatted}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Provider grid */}
      <div className="grid-2">
        {providers.map((p) => (
          <StorageCard
            key={p.id}
            provider={p}
            onConnect={handleConnect}
            onDisconnect={handleDisconnect}
            onExploreLocal={() => setExploreLocalModal(true)}
            onShowDetails={(prov) => setDetailsModalProvider(prov)}
          />
        ))}
      </div>

      {/* Info */}
      <div className="card-base" style={{ padding: '20px 24px', marginTop: 24, borderLeft: '3px solid var(--color-primary)', display: 'flex', gap: 14, alignItems: 'flex-start' }}>
        <i className="bi bi-shield-lock" style={{ fontSize: 22, color: 'var(--color-primary)', flexShrink: 0, marginTop: 2 }} />
        <div>
          <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--color-text-primary)', marginBottom: 4 }}>Privacy & Security</div>
          <div style={{ fontSize: 13, color: 'var(--color-text-secondary)', lineHeight: 1.6 }}>
            This application uses read-only access to your storage providers and local directories. We never modify, move, or delete your files.
            All cloud connections are handled securely through OAuth 2.0 with encrypted credentials.
          </div>
        </div>
      </div>

      {/* Connect modal */}
      {connectModal && (
        <ConnectStorageModal
          provider={connectModal}
          onConfirm={handleConfirmConnect}
          onClose={() => setConnectModal(null)}
        />
      )}

      {/* Local Drive Explorer Modal */}
      {exploreLocalModal && (
        <LocalDriveExplorerModal
          onClose={() => setExploreLocalModal(false)}
        />
      )}

      {/* Drive Details & Files Modal */}
      {detailsModalProvider && (
        <DriveFilesModal
          provider={detailsModalProvider}
          onClose={() => setDetailsModalProvider(null)}
        />
      )}
    </div>
  );
}
