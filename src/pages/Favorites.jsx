import React, { useEffect, useState } from 'react';
import { useApp } from '../context/AppContext';
import { listFiles } from '../services/fileService';
import { mockFiles } from '../data/mockData';
import FileCard from '../components/FileCard';
import EmptyState from '../components/EmptyState';
import { useNavigate } from 'react-router-dom';

export default function Favorites() {
  const { user, favorites, isFavorite } = useApp();
  const navigate = useNavigate();
  const isDemo = user?.email === 'meens@example.com';
  const [allFiles, setAllFiles] = useState(isDemo ? mockFiles : []);

  useEffect(() => {
    let isMounted = true;
    listFiles().then((data) => {
      if (isMounted) setAllFiles(data || []);
    });
    return () => { isMounted = false; };
  }, [user?.email]);

  const favoriteFiles = allFiles.filter((f) => isFavorite(f.id));

  return (
    <div>
      <div className="page-header">
        <div className="flex-between">
          <div>
            <h1 className="page-title">
              <i className="bi bi-star-fill" style={{ color: '#f59e0b', marginRight: 10 }} />
              Favorite Files
            </h1>
            <p className="page-subtitle">
              Files you've starred for quick access. Click the star icon on any file to favorite it.
            </p>
          </div>
          <div style={{ fontSize: 13, color: 'var(--color-text-muted)' }}>
            {favoriteFiles.length} file{favoriteFiles.length !== 1 ? 's' : ''}
          </div>
        </div>
      </div>

      {favoriteFiles.length === 0 ? (
        <EmptyState
          icon="bi-star"
          title="No favorites yet"
          description="Star files to add them here for quick access. Click the star icon on any file card."
          action={
            <button className="btn-primary-custom" onClick={() => navigate('/files')}>
              <i className="bi bi-folder2-open" /> Browse Files
            </button>
          }
        />
      ) : (
        <div className="grid-2">
          {favoriteFiles.map((f) => (
            <FileCard key={f.id} file={f} view="grid" />
          ))}
        </div>
      )}

      {favoriteFiles.length > 0 && (
        <div className="card-base" style={{ padding: '14px 18px', marginTop: 20, display: 'flex', alignItems: 'center', gap: 10 }}>
          <i className="bi bi-info-circle" style={{ color: 'var(--color-primary)', fontSize: 16 }} />
          <span style={{ fontSize: 13, color: 'var(--color-text-secondary)' }}>
            Favorites are saved locally. When the backend is integrated, favorites will sync across devices.
          </span>
        </div>
      )}
    </div>
  );
}
