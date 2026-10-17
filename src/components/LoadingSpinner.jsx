import React from 'react';

export default function LoadingSpinner({ message = 'Loading...' }) {
  return (
    <div className="loading-spinner" style={{ flexDirection: 'column', gap: 12 }}>
      <div className="spinner" />
      {message && (
        <span style={{ fontSize: 13, color: 'var(--color-text-muted)' }}>{message}</span>
      )}
    </div>
  );
}
