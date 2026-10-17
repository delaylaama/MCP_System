import React from 'react';

export default function EmptyState({
  icon = 'bi-inbox',
  title = 'Nothing here',
  description = '',
  action = null,
}) {
  return (
    <div className="empty-state">
      <div className="empty-state-icon">
        <i className={`bi ${icon}`} />
      </div>
      <div className="empty-state-title">{title}</div>
      {description && <div className="empty-state-desc">{description}</div>}
      {action && <div style={{ marginTop: 20 }}>{action}</div>}
    </div>
  );
}
