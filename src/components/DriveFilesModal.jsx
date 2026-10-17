import React, { useState, useEffect } from 'react';
import { listFiles, downloadFile } from '../services/fileService';
import FilePreviewModal from './FilePreviewModal';
import { ProviderStorageIcon } from './ProviderIcon';
import toast from 'react-hot-toast';

export default function DriveFilesModal({ provider, onClose }) {
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('');
  const [selectedFileForPreview, setSelectedFileForPreview] = useState(null);

  useEffect(() => {
    let isMounted = true;
    setLoading(true);

    const providerKey = provider.id || provider.provider || 'local';
    listFiles({ provider: providerKey, sort: 'latest' })
      .then((data) => {
        if (isMounted) setFiles(data || []);
      })
      .catch((err) => {
        console.warn('Error loading drive files:', err);
      })
      .finally(() => {
        if (isMounted) setLoading(false);
      });

    return () => { isMounted = false; };
  }, [provider]);

  const handleDownload = async (file) => {
    toast.loading(`Downloading ${file.name}...`, { id: `dl-${file.id}` });
    const res = await downloadFile(file.id);
    if (res.success) {
      toast.success(`Downloaded ${file.name}`, { id: `dl-${file.id}` });
    } else {
      toast.error(res.error || 'Download failed', { id: `dl-${file.id}` });
    }
  };

  const filteredFiles = files.filter((f) =>
    (f.name || '').toLowerCase().includes(filter.toLowerCase())
  );

  return (
    <>
      <div className="modal-overlay" onClick={onClose} style={{ zIndex: 1150 }}>
        <div
          className="modal-box"
          onClick={(e) => e.stopPropagation()}
          style={{
            width: '92%',
            maxWidth: 960,
            maxHeight: '88vh',
            display: 'flex',
            flexDirection: 'column',
            padding: 0,
            overflow: 'hidden',
            borderRadius: 16,
          }}
        >
          {/* Header */}
          <div
            style={{
              padding: '18px 24px',
              borderBottom: '1px solid var(--color-border)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              background: 'var(--color-surface)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
              <ProviderStorageIcon provider={provider.name} />
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <h3 style={{ margin: 0, fontSize: 16, fontWeight: 700, color: 'var(--color-text-primary)' }}>
                    {provider.name} Details & Files
                  </h3>
                  <span className="badge-connected" style={{ fontSize: 11, padding: '2px 8px' }}>
                    Connected
                  </span>
                </div>
                <div style={{ fontSize: 12, color: 'var(--color-text-muted)', marginTop: 2 }}>
                  {provider.usedStorage || '0 B'} used of {provider.totalStorage || 'N/A'} • {files.length} indexed files
                </div>
              </div>
            </div>
            <button
              onClick={onClose}
              style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: 24, color: 'var(--color-text-muted)' }}
            >
              <i className="bi bi-x" />
            </button>
          </div>

          {/* Storage Usage Bar & Toolbar */}
          <div style={{ padding: '12px 24px', background: 'var(--color-surface-2)', borderBottom: '1px solid var(--color-border)' }}>
            <div className="storage-usage-bar" style={{ height: 6, marginBottom: 12 }}>
              <div
                className="storage-usage-fill"
                style={{
                  width: `${provider.usedPercent || 0}%`,
                  background: provider.usedPercent > 80 ? 'var(--color-danger)' : 'var(--color-primary)',
                }}
              />
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 10 }}>
              <div style={{ fontSize: 12, color: 'var(--color-text-muted)' }}>
                Displaying files synchronized from {provider.name}.
              </div>
              <div className="input-group-custom" style={{ width: 240, marginBottom: 0 }}>
                <i className="bi bi-search input-icon" style={{ fontSize: 13 }} />
                <input
                  type="text"
                  className="form-control-custom"
                  placeholder="Filter files..."
                  style={{ padding: '5px 10px 5px 30px', fontSize: 12.5 }}
                  value={filter}
                  onChange={(e) => setFilter(e.target.value)}
                />
              </div>
            </div>
          </div>

          {/* Files List Table */}
          <div style={{ flex: 1, overflowY: 'auto', padding: '16px 24px', minHeight: 320 }}>
            {loading ? (
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: 240 }}>
                <div className="spinner-border text-primary" role="status" style={{ width: 32, height: 32 }}>
                  <span className="visually-hidden">Loading...</span>
                </div>
                <span style={{ marginTop: 12, fontSize: 13, color: 'var(--color-text-muted)' }}>
                  Loading files from {provider.name}...
                </span>
              </div>
            ) : filteredFiles.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '40px 0', color: 'var(--color-text-muted)' }}>
                <i className="bi bi-folder2-open" style={{ fontSize: 38, opacity: 0.6 }} />
                <p style={{ marginTop: 12, fontSize: 13.5 }}>
                  {filter ? `No files match "${filter}".` : 'No files found for this storage provider.'}
                </p>
              </div>
            ) : (
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid var(--color-border)', color: 'var(--color-text-muted)', fontSize: 11.5, textTransform: 'uppercase' }}>
                    <th style={{ padding: '8px 12px', textAlign: 'left' }}>File Name</th>
                    <th style={{ padding: '8px 12px', textAlign: 'left', width: 110 }}>Size</th>
                    <th style={{ padding: '8px 12px', textAlign: 'left', width: 140 }}>Modified</th>
                    <th style={{ padding: '8px 12px', textAlign: 'right', width: 140 }}>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredFiles.map((f) => (
                    <tr
                      key={f.id}
                      style={{
                        borderBottom: '1px solid var(--color-border)',
                        transition: 'background 0.15s ease',
                      }}
                      onMouseEnter={(e) => { e.currentTarget.style.background = 'var(--color-surface-2)'; }}
                      onMouseLeave={(e) => { e.currentTarget.style.background = 'transparent'; }}
                    >
                      <td style={{ padding: '10px 12px', display: 'flex', alignItems: 'center', gap: 10 }}>
                        <i className="bi bi-file-earmark-text text-primary" style={{ fontSize: 17 }} />
                        <span
                          style={{
                            fontWeight: 500,
                            color: 'var(--color-text-primary)',
                            whiteSpace: 'nowrap',
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                            maxWidth: 380,
                          }}
                        >
                          {f.name}
                        </span>
                      </td>
                      <td style={{ padding: '10px 12px', color: 'var(--color-text-secondary)', fontSize: 12 }}>
                        {f.size || '—'}
                      </td>
                      <td style={{ padding: '10px 12px', color: 'var(--color-text-muted)', fontSize: 12 }}>
                        {f.modified_at ? new Date(f.modified_at).toLocaleDateString() : '—'}
                      </td>
                      <td style={{ padding: '10px 12px', textAlign: 'right' }}>
                        <div style={{ display: 'inline-flex', gap: 6 }}>
                          <button
                            onClick={() => setSelectedFileForPreview(f)}
                            className="btn-outline-custom"
                            style={{ padding: '4px 10px', fontSize: 12, display: 'inline-flex', alignItems: 'center', gap: 4 }}
                            title="View File"
                          >
                            <i className="bi bi-eye" /> View
                          </button>
                          <button
                            onClick={() => handleDownload(f)}
                            className="btn-outline-custom"
                            style={{ padding: '4px 8px', fontSize: 12, color: 'var(--color-primary)' }}
                            title="Download File"
                          >
                            <i className="bi bi-download" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>

          {/* Footer */}
          <div
            style={{
              padding: '12px 24px',
              borderTop: '1px solid var(--color-border)',
              background: 'var(--color-surface)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              fontSize: 12,
              color: 'var(--color-text-muted)',
            }}
          >
            <span>{filteredFiles.length} item{filteredFiles.length !== 1 ? 's' : ''} listed</span>
            <button className="btn-outline-custom" onClick={onClose} style={{ padding: '6px 16px', fontSize: 12.5 }}>
              Close
            </button>
          </div>
        </div>
      </div>

      {/* File Preview Modal */}
      {selectedFileForPreview && (
        <FilePreviewModal
          file={selectedFileForPreview}
          onClose={() => setSelectedFileForPreview(null)}
        />
      )}
    </>
  );
}
