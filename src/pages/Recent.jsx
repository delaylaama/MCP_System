import React, { useEffect, useState } from 'react';
import { getRecentFiles } from '../services/fileService';
import FileCard from '../components/FileCard';
import LoadingSpinner from '../components/LoadingSpinner';
import EmptyState from '../components/EmptyState';

export default function Recent() {
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;
    getRecentFiles().then((data) => {
      if (isMounted) {
        setFiles(data);
        setLoading(false);
      }
    });
    return () => { isMounted = false; };
  }, []);

  if (loading) return <LoadingSpinner message="Loading recent files..." />;

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">
          <i className="bi bi-clock-history" style={{ color: 'var(--color-primary)', marginRight: 10 }} />
          Recently Accessed
        </h1>
        <p className="page-subtitle">Files you've opened or viewed recently across all providers.</p>
      </div>

      {files.length === 0 ? (
        <EmptyState
          icon="bi-clock"
          title="No recent files"
          description="Files you access will appear here for quick access."
        />
      ) : (
        <>
          <div style={{ marginBottom: 16 }}>
            <div className="card-base" style={{ overflow: 'hidden' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 14, padding: '10px 16px', borderBottom: '1px solid var(--color-border)', background: 'var(--color-surface-2)' }}>
                <div style={{ width: 40 }} />
                <div style={{ flex: 1, fontSize: 11, fontWeight: 600, color: 'var(--color-text-muted)', textTransform: 'uppercase' }}>File Name</div>
                <div style={{ minWidth: 120, fontSize: 11, fontWeight: 600, color: 'var(--color-text-muted)', textTransform: 'uppercase' }}>Provider</div>
                <div style={{ minWidth: 80, fontSize: 11, fontWeight: 600, color: 'var(--color-text-muted)', textTransform: 'uppercase' }}>Size</div>
                <div style={{ minWidth: 80 }} />
              </div>
              {files.map((f) => (
                <FileCard key={f.id} file={f} view="list" />
              ))}
            </div>
          </div>

          <div style={{ fontSize: 12.5, color: 'var(--color-text-muted)', textAlign: 'center' }}>
            <i className="bi bi-info-circle" style={{ marginRight: 6 }} />
            Showing {files.length} recently accessed files
          </div>
        </>
      )}
    </div>
  );
}
