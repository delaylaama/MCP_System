import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getFileMetadata, downloadFile, getFileContent } from '../services/fileService';
import { FILE_TYPES } from '../data/mockData';
import { useApp } from '../context/AppContext';
import ProviderIcon from '../components/ProviderIcon';
import LoadingSpinner from '../components/LoadingSpinner';
import EmptyState from '../components/EmptyState';
import toast from 'react-hot-toast';

export default function FileDetails() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { isFavorite, toggleFavorite } = useApp();
  const [file, setFile] = useState(null);
  const [contentPreview, setContentPreview] = useState(null);
  const [loading, setLoading] = useState(true);
  const [downloading, setDownloading] = useState(false);

  useEffect(() => {
    let isMounted = true;
    setLoading(true);
    getFileMetadata(id)
      .then((data) => {
        if (isMounted) setFile(data);
        if (data?.content_available) {
          getFileContent(id).then((content) => {
            if (isMounted) setContentPreview(content);
          });
        }
      })
      .finally(() => {
        if (isMounted) setLoading(false);
      });
    return () => { isMounted = false; };
  }, [id]);

  if (loading) return <LoadingSpinner message="Loading file details..." />;

  if (!file) {
    return (
      <EmptyState
        icon="bi-file-earmark-x"
        title="File not found"
        description="This file doesn't exist or has been removed."
        action={
          <button className="btn-primary-custom" onClick={() => navigate('/files')}>
            <i className="bi bi-arrow-left" /> Back to Files
          </button>
        }
      />
    );
  }

  const fileType = FILE_TYPES[file.type] || { label: file.type?.toUpperCase() || 'FILE', icon: 'bi-file-earmark' };
  const fav = isFavorite(file.id);

  const handleFavorite = () => {
    toggleFavorite(file.id);
    toast.success(fav ? 'Removed from favorites' : 'Added to favorites');
  };

  const handleDownload = async () => {
    setDownloading(true);
    try {
      const res = await downloadFile(file.id);
      if (res.success) {
        toast.success(`Downloaded ${res.filename || file.name}`);
      } else {
        toast.error(res.error || 'Download failed');
      }
    } catch {
      toast.error('Download failed');
    } finally {
      setDownloading(false);
    }
  };

  const handleOpenFile = () => {
    if (file.web_url) {
      window.open(file.web_url, '_blank');
    } else {
      toast(`Local file located at: ${file.path || file.name}`);
    }
  };

  return (
    <div className="file-details-page">
      {/* Back */}
      <button
        className="btn-outline-custom"
        style={{ marginBottom: 20 }}
        onClick={() => navigate(-1)}
      >
        <i className="bi bi-arrow-left" /> Back
      </button>

      {/* Header */}
      <div className="card-base file-details-header">
        <div className={`file-type-badge ${file.type}`} style={{ width: 56, height: 56, fontSize: 12 }}>
          {fileType.label}
        </div>
        <div style={{ flex: 1 }}>
          <h1 style={{ fontSize: 20, fontWeight: 700, color: 'var(--color-text-primary)', marginBottom: 8 }}>
            {file.name}
          </h1>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
            <ProviderIcon provider={file.provider} showLabel />
            <span style={{ fontSize: 12.5, color: 'var(--color-text-muted)' }}>
              <i className="bi bi-hdd" style={{ marginRight: 4 }} />{file.size}
            </span>
            <span style={{ fontSize: 12.5, color: 'var(--color-text-muted)' }}>
              <i className="bi bi-clock" style={{ marginRight: 4 }} />Modified {file.modified}
            </span>
          </div>
        </div>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'flex-start' }}>
          <button
            className={`favorite-btn ${fav ? 'active' : ''}`}
            onClick={handleFavorite}
            style={{ fontSize: 20 }}
            title={fav ? 'Remove from favorites' : 'Add to favorites'}
          >
            <i className={`bi ${fav ? 'bi-star-fill' : 'bi-star'}`} />
          </button>
        </div>
      </div>

      {/* Actions */}
      <div style={{ display: 'flex', gap: 10, marginBottom: 20, flexWrap: 'wrap' }}>
        <button
          className="btn-primary-custom"
          onClick={handleOpenFile}
        >
          <i className="bi bi-box-arrow-up-right" /> Open File
        </button>
        <button
          className="btn-outline-custom"
          onClick={handleDownload}
          disabled={downloading}
        >
          <i className="bi bi-download" /> {downloading ? 'Downloading...' : 'Download'}
        </button>
        <button
          className="btn-outline-custom"
          onClick={handleFavorite}
        >
          <i className={`bi ${fav ? 'bi-star-fill' : 'bi-star'}`} style={{ color: fav ? '#f59e0b' : undefined }} />
          {fav ? 'Remove Favorite' : 'Add to Favorites'}
        </button>
        <button
          className="btn-outline-custom"
          onClick={() => toast('Share feature coming soon!', { icon: '🔗' })}
        >
          <i className="bi bi-share" /> Share
        </button>
      </div>

      {/* Metadata */}
      <div className="card-base file-details-meta-card">
        <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--color-text-primary)', marginBottom: 16 }}>
          File Information
        </div>
        {[
          { key: 'File Name', value: file.name, icon: 'bi-file-earmark' },
          { key: 'File Type', value: fileType.label, icon: 'bi-tag' },
          { key: 'Location', value: file.provider, icon: 'bi-cloud' },
          { key: 'Path', value: file.path, icon: 'bi-folder' },
          { key: 'Size', value: file.size, icon: 'bi-hdd' },
          { key: 'Modified', value: file.modified, icon: 'bi-pencil' },
          { key: 'Created', value: file.created, icon: 'bi-calendar-plus' },
          { key: 'Last Opened', value: file.lastOpened, icon: 'bi-clock-history' },
        ].map((row) => (
          <div key={row.key} className="file-details-meta-row">
            <div className="file-details-meta-key">
              <i className={`bi ${row.icon}`} style={{ marginRight: 6, color: 'var(--color-text-muted)' }} />
              {row.key}
            </div>
            <div className="file-details-meta-value">{row.value}</div>
          </div>
        ))}

        {/* Tags */}
        {file.tags && file.tags.length > 0 && (
          <div className="file-details-meta-row">
            <div className="file-details-meta-key">
              <i className="bi bi-tags" style={{ marginRight: 6, color: 'var(--color-text-muted)' }} />
              Tags
            </div>
            <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
              {file.tags.map((t) => (
                <span key={t} className="tag">{t}</span>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* AI Summary */}
      <div className="card-base ai-summary-card">
        <div className="ai-summary-header">
          <i className="bi bi-stars" />
          AI Summary
          <span className="tag" style={{ marginLeft: 'auto', fontSize: 10 }}>Powered by MCP</span>
        </div>
        <p style={{ fontSize: 14, color: 'var(--color-text-secondary)', lineHeight: 1.7, margin: 0 }}>
          {file.aiSummary || 'AI indexing and summary generation active for this file.'}
        </p>
      </div>

      {/* Content Preview */}
      {contentPreview && (
        <div className="card-base" style={{ padding: '20px', marginTop: 16 }}>
          <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--color-text-primary)', marginBottom: 12, display: 'flex', alignItems: 'center', gap: 8 }}>
            <i className="bi bi-file-text" style={{ color: 'var(--color-primary)' }} />
            File Content Preview
          </div>
          <pre
            style={{
              background: 'var(--color-surface-2)',
              padding: '14px',
              borderRadius: 'var(--radius-md)',
              fontSize: 12.5,
              color: 'var(--color-text-primary)',
              whiteSpace: 'pre-wrap',
              maxHeight: 350,
              overflowY: 'auto',
              fontFamily: 'monospace',
              border: '1px solid var(--color-border)',
            }}
          >
            {contentPreview}
          </pre>
        </div>
      )}
    </div>
  );
}
