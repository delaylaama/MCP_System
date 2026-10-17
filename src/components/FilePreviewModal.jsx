import React, { useState, useEffect } from 'react';
import { getFileMetadata, getFileContent, downloadFile } from '../services/fileService';
import toast from 'react-hot-toast';

export default function FilePreviewModal({ file, fileId, onClose }) {
  const [fileData, setFileData] = useState(file || null);
  const [content, setContent] = useState('');
  const [loading, setLoading] = useState(true);
  const [downloading, setDownloading] = useState(false);

  const effectiveId = fileData?.id || fileId;

  useEffect(() => {
    let isMounted = true;
    setLoading(true);

    const loadData = async () => {
      try {
        let meta = fileData;
        if (!meta && effectiveId) {
          meta = await getFileMetadata(effectiveId);
          if (isMounted) setFileData(meta);
        }

        if (meta?.id) {
          const txt = await getFileContent(meta.id);
          if (isMounted) setContent(txt || '');
        }
      } catch (err) {
        console.warn('Could not load full preview:', err);
      } finally {
        if (isMounted) setLoading(false);
      }
    };

    loadData();
    return () => { isMounted = false; };
  }, [effectiveId]);

  const handleDownload = async () => {
    if (!fileData?.id) return;
    setDownloading(true);
    try {
      const res = await downloadFile(fileData.id);
      if (res.success) {
        toast.success(`Downloaded ${fileData.name}`);
      } else {
        toast.error(res.error || 'Download failed');
      }
    } catch {
      toast.error('Download failed');
    } finally {
      setDownloading(false);
    }
  };

  const isImage = fileData?.extension && ['.png', '.jpg', '.jpeg', '.webp', '.gif', '.bmp'].includes(fileData.extension.toLowerCase());

  return (
    <div className="modal-overlay" onClick={onClose} style={{ zIndex: 1200 }}>
      <div
        className="modal-box"
        onClick={(e) => e.stopPropagation()}
        style={{
          width: '90%',
          maxWidth: 780,
          maxHeight: '85vh',
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
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, minWidth: 0 }}>
            <div
              style={{
                width: 40,
                height: 40,
                borderRadius: 8,
                background: 'rgba(59,130,246,0.1)',
                color: 'var(--color-primary)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: 20,
                flexShrink: 0,
              }}
            >
              <i className={isImage ? 'bi bi-file-earmark-image-fill' : 'bi bi-file-earmark-text-fill'} />
            </div>
            <div style={{ minWidth: 0 }}>
              <h3
                style={{
                  margin: 0,
                  fontSize: 15,
                  fontWeight: 700,
                  color: 'var(--color-text-primary)',
                  whiteSpace: 'nowrap',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  maxWidth: 500,
                }}
              >
                {fileData?.name || 'File Preview'}
              </h3>
              <div style={{ fontSize: 12, color: 'var(--color-text-muted)', display: 'flex', gap: 8 }}>
                <span>Source: <strong>{fileData?.provider || 'local'}</strong></span>
                <span>•</span>
                <span>Size: {fileData?.size_formatted || fileData?.size || '—'}</span>
              </div>
            </div>
          </div>
          <button
            onClick={onClose}
            style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: 22, color: 'var(--color-text-muted)' }}
          >
            <i className="bi bi-x" />
          </button>
        </div>

        {/* Preview Content Area */}
        <div style={{ flex: 1, overflowY: 'auto', padding: 20, background: 'var(--color-surface-2)', minHeight: 260 }}>
          {loading ? (
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: 220 }}>
              <div className="spinner-border text-primary" role="status" style={{ width: 30, height: 30 }}>
                <span className="visually-hidden">Loading...</span>
              </div>
              <span style={{ marginTop: 10, fontSize: 12.5, color: 'var(--color-text-muted)' }}>Loading preview...</span>
            </div>
          ) : content ? (
            <div>
              <div style={{ fontSize: 11.5, fontWeight: 600, color: 'var(--color-text-muted)', textTransform: 'uppercase', marginBottom: 8 }}>
                Extracted Text & Document Content
              </div>
              <pre
                style={{
                  margin: 0,
                  padding: 16,
                  borderRadius: 8,
                  background: 'var(--color-surface)',
                  border: '1px solid var(--color-border)',
                  fontSize: 12.5,
                  lineHeight: 1.6,
                  whiteSpace: 'pre-wrap',
                  wordBreak: 'break-word',
                  fontFamily: 'Consolas, Monaco, monospace',
                  color: 'var(--color-text-primary)',
                  maxHeight: 380,
                  overflowY: 'auto',
                }}
              >
                {content}
              </pre>
            </div>
          ) : isImage ? (
            <div style={{ textAlign: 'center', padding: '30px 0' }}>
              <i className="bi bi-image" style={{ fontSize: 48, color: 'var(--color-primary)', opacity: 0.8 }} />
              <p style={{ marginTop: 12, fontSize: 13, color: 'var(--color-text-secondary)' }}>
                Visual embedding generated and indexed locally via CLIP ViT-B/32.
              </p>
              <p style={{ fontSize: 12, color: 'var(--color-text-muted)' }}>
                Path: {fileData?.path || fileData?.name}
              </p>
            </div>
          ) : (
            <div style={{ textAlign: 'center', padding: '40px 0', color: 'var(--color-text-muted)' }}>
              <i className="bi bi-file-earmark-check" style={{ fontSize: 40, opacity: 0.6 }} />
              <p style={{ marginTop: 12, fontSize: 13.5 }}>
                Metadata and file information indexed in local search database.
              </p>
              <p style={{ fontSize: 12, color: 'var(--color-text-muted)' }}>
                Path: {fileData?.path || fileData?.name}
              </p>
            </div>
          )}
        </div>

        {/* Footer Actions */}
        <div
          style={{
            padding: '12px 20px',
            borderTop: '1px solid var(--color-border)',
            background: 'var(--color-surface)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: 10,
          }}
        >
          <div style={{ fontSize: 12, color: 'var(--color-text-muted)' }}>
            {fileData?.modified_at ? `Modified: ${new Date(fileData.modified_at).toLocaleDateString()}` : ''}
          </div>
          <div style={{ display: 'flex', gap: 10 }}>
            {fileData?.web_url && (
              <a
                href={fileData.web_url}
                target="_blank"
                rel="noreferrer"
                className="btn-outline-custom"
                style={{ fontSize: 12, padding: '6px 12px', display: 'flex', alignItems: 'center', gap: 6 }}
              >
                <i className="bi bi-box-arrow-up-right" /> Open in Web
              </a>
            )}
            <button
              onClick={handleDownload}
              disabled={downloading}
              className="btn-primary-custom"
              style={{ fontSize: 12, padding: '6px 14px', display: 'flex', alignItems: 'center', gap: 6 }}
            >
              <i className="bi bi-download" /> {downloading ? 'Downloading...' : 'Download File'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
