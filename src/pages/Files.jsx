import React, { useEffect, useState } from 'react';
import { listFiles } from '../services/fileService';
import FileCard from '../components/FileCard';
import FilterBar from '../components/FilterBar';
import LoadingSpinner from '../components/LoadingSpinner';
import EmptyState from '../components/EmptyState';

export default function Files() {
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [provider, setProvider] = useState('all');
  const [sort, setSort] = useState('latest');
  const [view, setView] = useState('grid');
  const [search, setSearch] = useState('');

  useEffect(() => {
    let isMounted = true;
    const load = async () => {
      setLoading(true);
      try {
        const data = await listFiles({ provider, sort, search });
        if (isMounted) setFiles(data);
      } finally {
        if (isMounted) setLoading(false);
      }
    };
    load();
    return () => { isMounted = false; };
  }, [provider, sort, search]);

  return (
    <div>
      <div className="page-header">
        <div className="flex-between">
          <div>
            <h1 className="page-title">My Files</h1>
            <p className="page-subtitle">Browse and manage all your files across storage providers.</p>
          </div>
          <div style={{ fontSize: 13, color: 'var(--color-text-muted)' }}>
            {!loading && <span>{files.length} file{files.length !== 1 ? 's' : ''}</span>}
          </div>
        </div>
      </div>

      <FilterBar
        activeProvider={provider}
        onProviderChange={setProvider}
        sort={sort}
        onSortChange={setSort}
        view={view}
        onViewChange={setView}
        search={search}
        onSearchChange={setSearch}
      />

      {loading ? (
        <LoadingSpinner message="Loading your files..." />
      ) : files.length === 0 ? (
        <EmptyState
          icon="bi-folder-x"
          title="No files found"
          description={search ? `No files match "${search}". Try a different search term.` : 'No files found for the selected filter.'}
        />
      ) : view === 'grid' ? (
        <div className="grid-2">
          {files.map((f) => (
            <FileCard key={f.id} file={f} view="grid" />
          ))}
        </div>
      ) : (
        <div className="card-base" style={{ overflow: 'hidden' }}>
          {/* List header */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 14, padding: '10px 16px', borderBottom: '1px solid var(--color-border)', background: 'var(--color-surface-2)' }}>
            <div style={{ width: 40, fontSize: 11, fontWeight: 600, color: 'var(--color-text-muted)', textTransform: 'uppercase' }}>Type</div>
            <div style={{ flex: 1, fontSize: 11, fontWeight: 600, color: 'var(--color-text-muted)', textTransform: 'uppercase' }}>Name</div>
            <div style={{ minWidth: 100, fontSize: 11, fontWeight: 600, color: 'var(--color-text-muted)', textTransform: 'uppercase' }}>Provider</div>
            <div style={{ minWidth: 80, fontSize: 11, fontWeight: 600, color: 'var(--color-text-muted)', textTransform: 'uppercase' }}>Size</div>
            <div style={{ minWidth: 80, fontSize: 11, fontWeight: 600, color: 'var(--color-text-muted)', textTransform: 'uppercase' }}>Actions</div>
          </div>
          {files.map((f) => (
            <FileCard key={f.id} file={f} view="list" />
          ))}
        </div>
      )}
    </div>
  );
}
