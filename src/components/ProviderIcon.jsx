import React from 'react';
import { PROVIDERS } from '../data/mockData';

const baseConfig = {
  gdrive: {
    icon: 'bi-google',
    color: '#4285f4',
    bg: 'rgba(66,133,244,0.1)',
    cssClass: 'gdrive',
    short: 'GDrive',
  },
  onedrive: {
    icon: 'bi-microsoft',
    color: '#0078d4',
    bg: 'rgba(0,120,212,0.1)',
    cssClass: 'onedrive',
    short: 'OneDrive',
  },
  dropbox: {
    icon: 'bi-dropbox',
    color: '#0061ff',
    bg: 'rgba(0,97,255,0.1)',
    cssClass: 'dropbox',
    short: 'Dropbox',
  },
  local: {
    icon: 'bi-hdd',
    color: '#374151',
    bg: 'rgba(55,65,81,0.08)',
    cssClass: 'local',
    short: 'Local',
  },
};

const providerConfig = {
  [PROVIDERS.GOOGLE_DRIVE]: baseConfig.gdrive,
  google_drive: baseConfig.gdrive,
  'Google Drive': baseConfig.gdrive,
  [PROVIDERS.ONEDRIVE]: baseConfig.onedrive,
  onedrive: baseConfig.onedrive,
  OneDrive: baseConfig.onedrive,
  'Microsoft OneDrive': baseConfig.onedrive,
  [PROVIDERS.DROPBOX]: baseConfig.dropbox,
  dropbox: baseConfig.dropbox,
  Dropbox: baseConfig.dropbox,
  [PROVIDERS.LOCAL]: baseConfig.local,
  local: baseConfig.local,
  Local: baseConfig.local,
  'Local Storage': baseConfig.local,
  'Local Files': baseConfig.local,
};

export default function ProviderIcon({ provider, showLabel = false, size = 'sm', className = '' }) {
  const config = providerConfig[provider] || {
    icon: 'bi-cloud',
    color: '#6b7280',
    bg: 'rgba(107,114,128,0.1)',
    cssClass: 'local',
    short: provider,
  };

  const iconSize = size === 'lg' ? 20 : 14;

  return (
    <span className={`provider-badge ${config.cssClass} ${className}`}>
      <i className={`bi ${config.icon}`} style={{ fontSize: iconSize }} />
      {showLabel && <span>{provider}</span>}
    </span>
  );
}

export function ProviderStorageIcon({ provider, size = 44 }) {
  const config = providerConfig[provider] || {
    icon: 'bi-cloud',
    color: '#6b7280',
    bg: 'rgba(107,114,128,0.1)',
  };

  return (
    <div
      className="storage-provider-icon"
      style={{ width: size, height: size, background: config.bg }}
    >
      <i className={`bi ${config.icon}`} style={{ color: config.color, fontSize: size * 0.44 }} />
    </div>
  );
}

export { providerConfig };
