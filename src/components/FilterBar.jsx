import React, { useState } from 'react';
import { PROVIDERS } from '../data/mockData';

const providers = [
  { id: 'all', label: 'All' },
  { id: PROVIDERS.GOOGLE_DRIVE, label: 'Google Drive' },
  { id: PROVIDERS.ONEDRIVE, label: 'OneDrive' },
  { id: PROVIDERS.DROPBOX, label: 'Dropbox' },
  { id: PROVIDERS.LOCAL, label: 'Local' },
];

const sortOptions = [
  { id: 'latest', label: 'Latest' },
  { id: 'oldest', label: 'Oldest' },
  { id: 'name-asc', label: 'Name A–Z' },
  { id: 'name-desc', label: 'Name Z–A' },
  { id: 'size', label: 'Size' },
];

export default function FilterBar({
  activeProvider = 'all',
  onProviderChange,
  sort = 'latest',
  onSortChange,
  view = 'grid',
  onViewChange,
  search = '',
  onSearchChange,
}) {
  return (
    <div style={{ marginBottom: 20 }}>
      {/* Search + view + sort row */}
      <div className="flex-between" style={{ flexWrap: 'wrap', gap: 10, marginBottom: 12 }}>
        <div className="input-group-custom" style={{ flex: 1, maxWidth: 360 }}>
          <i className="bi bi-search input-icon" />
          <input
            type="text"
            className="form-control-custom"
            placeholder="Search files..."
            value={search}
            onChange={(e) => onSearchChange?.(e.target.value)}
          />
        </div>

        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          {/* Sort */}
          <select
            className="form-control-custom"
            style={{ width: 'auto', padding: '8px 32px 8px 12px', fontSize: 13 }}
            value={sort}
            onChange={(e) => onSortChange?.(e.target.value)}
          >
            {sortOptions.map((o) => (
              <option key={o.id} value={o.id}>{o.label}</option>
            ))}
          </select>

          {/* View toggle */}
          {onViewChange && (
            <div className="view-toggle">
              <button
                className={`view-toggle-btn ${view === 'grid' ? 'active' : ''}`}
                onClick={() => onViewChange('grid')}
                title="Grid view"
              >
                <i className="bi bi-grid-3x3-gap" />
              </button>
              <button
                className={`view-toggle-btn ${view === 'list' ? 'active' : ''}`}
                onClick={() => onViewChange('list')}
                title="List view"
              >
                <i className="bi bi-list-ul" />
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Provider filter chips */}
      <div className="filter-bar">
        {providers.map((p) => (
          <button
            key={p.id}
            className={`filter-btn ${activeProvider === p.id ? 'active' : ''}`}
            onClick={() => onProviderChange?.(p.id)}
          >
            {p.label}
          </button>
        ))}
      </div>
    </div>
  );
}
