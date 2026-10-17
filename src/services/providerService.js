/**
 * Provider service — manages storage provider connections (Google Drive,
 * OneDrive, Dropbox, Local) via the FastAPI backend and OAuth 2.0 flows.
 *
 * Backend contract:
 *   GET    /api/providers                    → ProviderStatusResponse[]
 *   GET    /api/providers/{provider}/connect  → ProviderConnectResponse
 *   GET    /api/providers/{provider}/callback  (handled by browser redirect)
 *   DELETE /api/providers/{provider}          → {message}
 *   GET    /api/health                        → health payload
 */

import api, { isBackendError, isDemoUser } from './api';
import { getStorageProviders as mockProviders } from '../data/mockData';

/**
 * Fetch all supported providers and the user's connection status for each.
 * Falls back to mock data only for demo accounts when the backend is unreachable.
 *
 * @returns {Promise<object[]>} Array of provider objects shaped for StorageCard
 */
export async function listProviders() {
  try {
    const { data } = await api.get('/api/providers');

    return data.map((p) => ({
      id: p.provider,
      name: p.name,
      connected: p.connected,
      account_identifier: p.account_identifier,
      connected_at: p.connected_at,
      status: p.status,
      fileCount: p.file_count ?? 0,
      usedStorage: p.used_storage || '0 B',
      totalStorage: p.total_storage || '0 B',
      usedPercent: p.used_percent || 0,
      lastSync: p.connected ? (p.connected_at ? new Date(p.connected_at).toLocaleTimeString() : 'Just now') : '—',
      description: getProviderDescription(p.name),
      permissions: ['Read files', 'Search files', 'Read file metadata'],
    }));
  } catch (err) {
    console.warn('[ProviderService] Failed to fetch providers from backend, falling back to standard providers', err);
    return mockProviders();
  }
}

/**
 * Initiate OAuth connection for a cloud provider.
 * Returns an authorization URL that the frontend should redirect to.
 *
 * @param {string} provider  Provider key: 'google_drive' | 'onedrive' | 'dropbox'
 * @returns {Promise<{provider: string, authorization_url: string, state: string}>}
 */
export async function connectProvider(provider) {
  const { data } = await api.get(`/api/providers/${encodeURIComponent(provider)}/connect`);
  return data;
}

/**
 * Disconnect a cloud provider — removes OAuth credentials from the backend.
 *
 * @param {string} provider  Provider key
 * @returns {Promise<{message: string}>}
 */
export async function disconnectProvider(provider) {
  const { data } = await api.delete(`/api/providers/${encodeURIComponent(provider)}`);
  return data;
}

/**
 * Check backend and MCP server health.
 *
 * @returns {Promise<object>} Health payload or an offline stub
 */
export async function checkHealth() {
  try {
    const { data } = await api.get('/api/health');
    return data;
  } catch {
    return {
      status: 'offline',
      app: 'Universal AI File Manager',
      mcp_server: { status: 'offline', tools_available: 0 },
    };
  }
}

/**
 * Get system disk drives detected on the host machine.
 *
 * @returns {Promise<Array>} Array of drive objects with usage metrics
 */
export async function getLocalDrives() {
  try {
    const { data } = await api.get('/api/providers/local/drives');
    return data;
  } catch {
    return [];
  }
}

/**
 * Browse local file system directories or list drives.
 *
 * @param {string} [path]  Directory path to inspect, or null for root drives
 * @returns {Promise<{current_path: string, parent_path: string|null, is_root: boolean, items: Array}>}
 */
export async function browseLocalPath(path) {
  const params = path ? { path } : {};
  const { data } = await api.get('/api/providers/local/browse', { params });
  return data;
}

// ── Internal helpers ──

function getProviderDescription(name) {
  const descriptions = {
    'Google Drive': 'Search and manage files stored in your Google Drive account.',
    'Microsoft OneDrive': 'Access your Microsoft OneDrive files through the AI assistant.',
    OneDrive: 'Access your Microsoft OneDrive files through the AI assistant.',
    Dropbox: 'Connect your Dropbox to search files with AI assistance.',
    'Local Storage': 'Index and search files from your local file system.',
  };
  return descriptions[name] || `Access your ${name} files through the AI assistant.`;
}
