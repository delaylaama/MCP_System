import React, { useState, useEffect } from 'react';
import { browseLocalPath, getLocalDrives } from '../services/providerService';
import { downloadFile } from '../services/fileService';
import FilePreviewModal from './FilePreviewModal';
import toast from 'react-hot-toast';

export default function LocalDriveExplorerModal({ onClose }) {
  const [currentPath, setCurrentPath] = useState('root');
  const [parentPath, setParentPath] = useState(null);
  const [isRoot, setIsRoot] = useState(true);
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('');
  const [drivesSummary, setDrivesSummary] = useState([]);
  const [previewFile, setPreviewFile] = useState(null);

  const loadDirectory = async (path = 'root') => {
    setLoading(true);
    setFilter('');
    try {
      const data = await browseLocalPath(path === 'root' ? null : path);
      setCurrentPath(data.current_path || path);
      setParentPath(data.parent_path);
      setIsRoot(data.is_root ?? (path === 'root'));
      setItems(data.items || []);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to open directory. Access might be restricted.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDirectory('root');
    getLocalDrives().then((d) => setDrivesSummary(d || []));
  }, []);

  const handleItemClick = (item) => {
    if (item.is_folder || item.is_drive) {
      loadDirectory(item.path);
    } else {
      handleDownload(item);
    }
  };

  const handleDownload = async (file) => {
    toast.loading(`Downloading ${file.name}...`, { id: `dl-${file.id}` });
    const res = await downloadFile(file.id);
    if (res.success) {
      toast.success(`Downloaded ${file.name}`, { id: `dl-${file.id}` });
    } else {
      toast.error(res.error || 'Download failed', { id: `dl-${file.id}` });
    }
  };

  const formatSize = (bytes) => {
    if (!bytes || bytes <= 0) return '0 B';
    const units = ['B', 'KB', 'MB', 'GB', 'TB'];
    let val = bytes;
    for (const unit of units) {
      if (val < 1024) return `${val < 10 ? val.toFixed(1) : Math.round(val)} ${unit}`;
      val /= 1024;
    }
    return `${val.toFixed(1)} PB`;
  };

  const getFileIcon = (ext, isFolder, isDrive) => {
    if (isDrive) return 'bi-hdd-fill text-primary';
    if (isFolder) return 'bi-folder-fill text-warning';
    const clean = (ext || '').toLowerCase().replace('.', '');
    switch (clean) {
      case 'pdf': return 'bi-file-earmark-pdf-fill text-danger';
      case 'docx':
      case 'doc': return 'bi-file-earmark-word-fill text-primary';
      case 'xlsx':
      case 'xls':
      case 'csv': return 'bi-file-earmark-excel-fill text-success';
      case 'pptx': return 'bi-file-earmark-ppt-fill text-warning';
      case 'png':
      case 'jpg':
      case 'jpeg':
      case 'gif': return 'bi-file-earmark-image-fill text-info';
      case 'zip':
      case 'rar':
      case '7z': return 'bi-file-earmark-zip-fill text-secondary';
      case 'py':
      case 'js':
      case 'jsx':
      case 'html':
      case 'css':
      case 'json': return 'bi-file-earmark-code-fill text-info';
      default: return 'bi-file-earmark-text text-muted';
    }
  };

  const filteredItems = items.filter((i) =>
    i.name.toLowerCase().includes(filter.toLowerCase())
  );

  // Compute breadcrumbs
  const renderBreadcrumbs = () => {
    if (isRoot || currentPath === 'root') {
      return (
        <span style={{ fontWeight: 600, color: 'var(--color-text-primary)' }}>
          <i className="bi bi-pc-display" style={{ marginRight: 6 }} /> This PC (System Drives)
        </span>
      );
    }

    const normalized = currentPath.replace(/\\/g, '/');
    const parts = normalized.split('/').filter(Boolean);

    return (
      <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap', fontSize: 13 }}>
        <button
          onClick={() => loadDirectory('root')}
          style={{ background: 'none', border: 'none', color: 'var(--color-primary)', cursor: 'pointer', padding: 0, fontWeight: 600 }}
        >
          <i className="bi bi-pc-display" /> This PC
        </button>
        {parts.map((part, idx) => {
          const subPath = parts.slice(0, idx + 1).join('/');
          const isLast = idx === parts.length - 1;
          const displayPart = idx === 0 && part.includes(':') ? `${part}\\` : part;

          return (
            <React.Fragment key={subPath}>
              <span style={{ color: 'var(--color-text-muted)' }}>/</span>
              {isLast ? (
                <span style={{ fontWeight: 600, color: 'var(--color-text-primary)' }}>{displayPart}</span>
              ) : (
                <button
                  onClick={() => loadDirectory(subPath)}
                  style={{ background: 'none', border: 'none', color: 'var(--color-primary)', cursor: 'pointer', padding: 0 }}
                >
                  {displayPart}
                </button>
              )}
            </React.Fragment>
          );
        })}
      </div>
    );
  };

  return (
    <div className="modal-overlay" onClick={onClose} style={{ zIndex: 1100 }}>
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
            padding: '16px 20px',
            borderBottom: '1px solid var(--color-border)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            background: 'var(--color-surface)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <div
              style={{
                width: 38,
                height: 38,
                borderRadius: 8,
                background: 'rgba(55,65,81,0.08)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'var(--color-text-primary)',
                fontSize: 18,
              }}
            >
              <i className="bi bi-hdd-network" />
            </div>
            <div>
              <h3 style={{ margin: 0, fontSize: 16, fontWeight: 700, color: 'var(--color-text-primary)' }}>
                Local System Drives & Explorer
              </h3>
              <p style={{ margin: 0, fontSize: 12, color: 'var(--color-text-muted)' }}>
                Browse system drives, project sandbox files, and directories.
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: 22, color: 'var(--color-text-muted)' }}
          >
            <i className="bi bi-x" />
          </button>
        </div>

        {/* Toolbar & Breadcrumbs */}
        <div
          style={{
            padding: '10px 20px',
            background: 'var(--color-surface-2)',
            borderBottom: '1px solid var(--color-border)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: 12,
            flexWrap: 'wrap',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, flex: 1, minWidth: 260 }}>
            {!isRoot && (
              <button
                className="btn-outline-custom"
                onClick={() => loadDirectory(parentPath || 'root')}
                style={{ padding: '4px 10px', fontSize: 12 }}
                title="Go to parent directory"
              >
                <i className="bi bi-arrow-up" /> Up
              </button>
            )}
            <div style={{ overflowX: 'auto', whiteSpace: 'nowrap', flex: 1 }}>
              {renderBreadcrumbs()}
            </div>
          </div>

          <div className="input-group-custom" style={{ width: 220, marginBottom: 0 }}>
            <i className="bi bi-search input-icon" style={{ fontSize: 13 }} />
            <input
              type="text"
              className="form-control-custom"
              placeholder="Filter items..."
              style={{ padding: '6px 12px 6px 32px', fontSize: 12.5 }}
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
            />
          </div>
        </div>

        {/* Content Body */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '18px 20px', minHeight: 340 }}>
          {loading ? (
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: 260 }}>
              <div className="spinner-border text-primary" role="status" style={{ width: 32, height: 32 }}>
                <span className="visually-hidden">Loading...</span>
              </div>
              <span style={{ marginTop: 12, fontSize: 13, color: 'var(--color-text-muted)' }}>Reading files & folders...</span>
            </div>
          ) : isRoot ? (
            /* System Drives Root View */
            <div>
              <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--color-text-secondary)', marginBottom: 14 }}>
                Detected System Disks ({drivesSummary.length} Drives)
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 14, marginBottom: 20 }}>
                {items.map((item) => {
                  const isDrive = item.is_drive;
                  return (
                    <div
                      key={item.id}
                      onClick={() => handleItemClick(item)}
                      className="card-base"
                      style={{
                        padding: 16,
                        cursor: 'pointer',
                        transition: 'all 0.2s ease',
                        border: '1px solid var(--color-border)',
                      }}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.borderColor = 'var(--color-primary)';
                        e.currentTarget.style.transform = 'translateY(-2px)';
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.borderColor = 'var(--color-border)';
                        e.currentTarget.style.transform = 'none';
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 10 }}>
                        <div
                          style={{
                            width: 44,
                            height: 44,
                            borderRadius: 10,
                            background: isDrive ? 'rgba(0,120,212,0.1)' : 'rgba(16,185,129,0.1)',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            fontSize: 22,
                            color: isDrive ? 'var(--color-primary)' : 'var(--color-success)',
                          }}
                        >
                          <i className={`bi ${isDrive ? 'bi-hdd-fill' : 'bi-folder-fill'}`} />
                        </div>
                        <div style={{ flex: 1, minWidth: 0 }}>
                          <div style={{ fontWeight: 700, fontSize: 14, color: 'var(--color-text-primary)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                            {item.name}
                          </div>
                          <div style={{ fontSize: 11.5, color: 'var(--color-text-muted)' }}>
                            {isDrive ? `${item.file_system || 'NTFS'} File System` : `${item.file_count || 0} indexed files`}
                          </div>
                        </div>
                      </div>

                      {isDrive && item.total_size > 0 && (
                        <>
                          <div className="storage-usage-bar" style={{ height: 6, margin: '10px 0 6px' }}>
                            <div
                              className="storage-usage-fill"
                              style={{
                                width: `${item.used_percent}%`,
                                background: item.used_percent > 85 ? 'var(--color-danger)' : item.used_percent > 70 ? 'var(--color-warning)' : 'var(--color-primary)',
                              }}
                            />
                          </div>
                          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11.5, color: 'var(--color-text-muted)' }}>
                            <span>{formatSize(item.free_size)} free</span>
                            <span>{item.used_percent}% used of {formatSize(item.total_size)}</span>
                          </div>
                        </>
                      )}

                      {!isDrive && (
                        <div style={{ fontSize: 12, color: 'var(--color-primary)', marginTop: 8, display: 'flex', alignItems: 'center', gap: 4 }}>
                          <i className="bi bi-box-arrow-in-right" /> Open sandbox directory
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          ) : filteredItems.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '40px 0', color: 'var(--color-text-muted)' }}>
              <i className="bi bi-folder2-open" style={{ fontSize: 36, opacity: 0.5 }} />
              <p style={{ marginTop: 10, fontSize: 14 }}>
                {filter ? `No items matching "${filter}"` : 'This folder is empty or contains only hidden system files.'}
              </p>
            </div>
          ) : (
            /* Directory Browser Items Table */
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid var(--color-border)', color: 'var(--color-text-muted)', fontSize: 11.5, textTransform: 'uppercase' }}>
                    <th style={{ padding: '8px 12px', textAlign: 'left' }}>Name</th>
                    <th style={{ padding: '8px 12px', textAlign: 'left', width: 110 }}>Size</th>
                    <th style={{ padding: '8px 12px', textAlign: 'left', width: 140 }}>Modified</th>
                    <th style={{ padding: '8px 12px', textAlign: 'right', width: 90 }}>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredItems.map((item) => {
                    const isDir = item.is_folder || item.is_drive;
                    return (
                      <tr
                        key={item.id}
                        onClick={() => isDir && handleItemClick(item)}
                        style={{
                          borderBottom: '1px solid var(--color-border)',
                          cursor: isDir ? 'pointer' : 'default',
                          transition: 'background 0.15s ease',
                        }}
                        onMouseEnter={(e) => { e.currentTarget.style.background = 'var(--color-surface-2)'; }}
                        onMouseLeave={(e) => { e.currentTarget.style.background = 'transparent'; }}
                      >
                        <td style={{ padding: '10px 12px', display: 'flex', alignItems: 'center', gap: 10 }}>
                          <i className={`bi ${getFileIcon(item.extension, isDir, item.is_drive)}`} style={{ fontSize: 18 }} />
                          <span
                            style={{
                              fontWeight: isDir ? 600 : 400,
                              color: isDir ? 'var(--color-primary)' : 'var(--color-text-primary)',
                              whiteSpace: 'nowrap',
                              overflow: 'hidden',
                              textOverflow: 'ellipsis',
                              maxWidth: 380,
                            }}
                          >
                            {item.name}
                          </span>
                        </td>
                        <td style={{ padding: '10px 12px', color: 'var(--color-text-secondary)', fontSize: 12 }}>
                          {isDir ? '—' : formatSize(item.size)}
                        </td>
                        <td style={{ padding: '10px 12px', color: 'var(--color-text-muted)', fontSize: 12 }}>
                          {item.modified_at ? new Date(item.modified_at).toLocaleDateString() : '—'}
                        </td>
                        <td style={{ padding: '10px 12px', textAlign: 'right' }}>
                          {isDir ? (
                            <button
                              onClick={(e) => { e.stopPropagation(); handleItemClick(item); }}
                              className="btn-outline-custom"
                              style={{ padding: '3px 8px', fontSize: 11.5 }}
                            >
                              Open
                            </button>
                          ) : (
                            <div style={{ display: 'inline-flex', gap: 6 }}>
                              <button
                                onClick={() => setPreviewFile(item)}
                                className="btn-outline-custom"
                                style={{ padding: '3px 8px', fontSize: 11.5, display: 'inline-flex', alignItems: 'center', gap: 4 }}
                                title="View File Preview"
                              >
                                <i className="bi bi-eye" /> View
                              </button>
                              <button
                                onClick={() => handleDownload(item)}
                                className="btn-outline-custom"
                                style={{ padding: '3px 8px', fontSize: 11.5, color: 'var(--color-primary)' }}
                                title="Download File"
                              >
                                <i className="bi bi-download" />
                              </button>
                            </div>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Footer */}
        <div
          style={{
            padding: '12px 20px',
            borderTop: '1px solid var(--color-border)',
            background: 'var(--color-surface)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            fontSize: 12,
            color: 'var(--color-text-muted)',
          }}
        >
          <span>
            {items.length} item{items.length !== 1 ? 's' : ''} in directory
          </span>
          <button className="btn-outline-custom" onClick={onClose} style={{ padding: '6px 14px', fontSize: 12.5 }}>
            Close Explorer
          </button>
        </div>
      </div>

      {/* File Preview Modal */}
      {previewFile && (
        <FilePreviewModal
          file={previewFile}
          onClose={() => setPreviewFile(null)}
        />
      )}
    </div>
  );
}
