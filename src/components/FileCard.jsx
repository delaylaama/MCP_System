import React from 'react';
import { useNavigate } from 'react-router-dom';
import { FILE_TYPES } from '../data/mockData';
import { downloadFile } from '../services/fileService';
import ProviderIcon from './ProviderIcon';
import { useApp } from '../context/AppContext';
import toast from 'react-hot-toast';

export default function FileCard({ file, view = 'grid' }) {
  const navigate = useNavigate();
  const { isFavorite, toggleFavorite } = useApp();

  const fileType = FILE_TYPES[file.type] || {
    label: file.type?.toUpperCase() || 'FILE',
    icon: 'bi-file-earmark',
    color: '#6b7280',
  };

  const handleOpen = (e) => {
    e.stopPropagation();
    navigate(`/file/${file.id}`);
  };

  const handleDownload = async (e) => {
    e.stopPropagation();
    toast.success(`Starting download for ${file.name}...`);
    try {
      const res = await downloadFile(file.id);
      if (res.error) toast.error(res.error);
    } catch {
      toast.error('Download failed.');
    }
  };

  const handleFavorite = (e) => {
    e.stopPropagation();
    toggleFavorite(file.id);
    toast.success(isFavorite(file.id) ? 'Removed from favorites' : 'Added to favorites');
  };

  const fav = isFavorite(file.id);

  if (view === 'list') {
    return (
      <div className="file-list-row" onClick={() => navigate(`/file/${file.id}`)}>
        {/* Type badge */}
        <div className={`file-type-badge ${file.type}`}>
          {fileType.label}
        </div>

        {/* Name */}
        <div className="file-list-name" title={file.name}>{file.name}</div>

        {/* Provider */}
        <div style={{ flexShrink: 0 }}>
          <ProviderIcon provider={file.provider} showLabel />
        </div>

        {/* Modified */}
        <div className="file-list-meta" style={{ display: 'none' }} data-hide-sm>
          {file.modified}
        </div>

        {/* Size */}
        <div className="file-list-meta">{file.size}</div>

        {/* Actions */}
        <div className="file-list-actions" onClick={(e) => e.stopPropagation()}>
          <button
            className={`favorite-btn ${fav ? 'active' : ''}`}
            onClick={handleFavorite}
            title={fav ? 'Remove from favorites' : 'Add to favorites'}
          >
            <i className={`bi ${fav ? 'bi-star-fill' : 'bi-star'}`} />
          </button>
          <button className="btn-icon-custom" onClick={handleDownload} title="Download">
            <i className="bi bi-download" />
          </button>
          <button className="btn-icon-custom" onClick={handleOpen} title="View details">
            <i className="bi bi-arrow-right" />
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="card-base card-hover file-card" onClick={() => navigate(`/file/${file.id}`)}>
      <div className="file-card-header">
        <div className={`file-type-badge ${file.type}`} style={{ width: 40, height: 40 }}>
          {fileType.label}
        </div>
        <div className="file-card-info">
          <div className="file-card-name" title={file.name}>{file.name}</div>
          <div className="file-card-meta">
            <ProviderIcon provider={file.provider} showLabel />
            <span>·</span>
            <span>{file.size}</span>
          </div>
        </div>
        <button
          className={`favorite-btn ${fav ? 'active' : ''}`}
          onClick={handleFavorite}
          title={fav ? 'Remove from favorites' : 'Add to favorites'}
          style={{ marginLeft: 'auto', flexShrink: 0 }}
        >
          <i className={`bi ${fav ? 'bi-star-fill' : 'bi-star'}`} />
        </button>
      </div>

      <div style={{ fontSize: 11.5, color: 'var(--color-text-muted)', display: 'flex', alignItems: 'center', gap: 5 }}>
        <i className="bi bi-clock" style={{ fontSize: 11 }} />
        Modified {file.modified}
      </div>

      <div className="file-card-actions" onClick={(e) => e.stopPropagation()}>
        <button className="btn-outline-custom" style={{ flex: 1, justifyContent: 'center', fontSize: 12.5, padding: '7px 10px' }} onClick={handleOpen}>
          <i className="bi bi-eye" /> View
        </button>
        <button className="btn-outline-custom" style={{ flex: 1, justifyContent: 'center', fontSize: 12.5, padding: '7px 10px' }} onClick={handleDownload}>
          <i className="bi bi-download" /> Download
        </button>
      </div>
    </div>
  );
}
