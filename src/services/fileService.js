/**
 * File service — single-file metadata, content preview, download, duplicates,
 * and a general "list files" helper that uses the search endpoint under the
 * hood (the backend does not expose a dedicated file-listing route).
 *
 * Backend contract:
 *   GET /api/files/{id}           → FileRecord
 *   GET /api/files/{id}/content   → {id, content}
 *   GET /api/files/{id}/download  → StreamingResponse (binary)
 *   GET /api/files/duplicates     → DuplicateGroup[]
 */

import api, { isBackendError, isDemoUser } from './api';
import { normalizeFile } from './searchService';

// Map display-name provider strings back to API keys
const PROVIDER_KEY = {
  'Google Drive': 'google_drive',
  'google_drive': 'google_drive',
  OneDrive: 'onedrive',
  'onedrive': 'onedrive',
  Dropbox: 'dropbox',
  'dropbox': 'dropbox',
  Local: 'local',
  'Local Storage': 'local',
  'Local Files': 'local',
  'local': 'local',
};

/**
 * Fetch metadata for a single file from the backend.
 * Falls back to mock data only for demo account when the backend is unreachable.
 *
 * @param {string} id  Internal composite file ID (e.g. "local_abc123")
 * @returns {Promise<object>} Normalized file object
 */
export async function getFileMetadata(id) {
  try {
    const { data } = await api.get(`/api/files/${encodeURIComponent(id)}`);
    return normalizeFile(data);
  } catch (err) {
    if (isBackendError(err)) throw err;
    if (isDemoUser()) {
      console.warn('[FileService] Backend offline, falling back to mock data for demo user');
      const { getFileById } = await import('../data/mockData');
      return getFileById(id);
    }
    return null;
  }
}

/**
 * Fetch plain-text content preview for a file.
 *
 * @param {string} id
 * @returns {Promise<string|null>}
 */
export async function getFileContent(id) {
  try {
    const { data } = await api.get(`/api/files/${encodeURIComponent(id)}/content`);
    return data.content;
  } catch (err) {
    if (isBackendError(err)) throw err;
    return null;
  }
}

/**
 * Download a file by triggering a browser download (creates a temporary <a> element).
 *
 * @param {string} id
 * @returns {Promise<{success: boolean, filename?: string, error?: string}>}
 */
export async function downloadFile(id) {
  try {
    const response = await api.get(`/api/files/${encodeURIComponent(id)}/download`, {
      responseType: 'blob',
    });

    // Extract filename from Content-Disposition header
    const disposition = response.headers['content-disposition'];
    let filename = 'download';
    if (disposition) {
      const match = disposition.match(/filename="?([^"]+)"?/);
      if (match) filename = match[1];
    }

    // Trigger browser download
    const url = window.URL.createObjectURL(response.data);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);

    return { success: true, filename };
  } catch (err) {
    if (isBackendError(err)) {
      return {
        success: false,
        error: err.response?.data?.detail || 'Download failed.',
      };
    }
    return { success: false, error: 'Backend offline — download unavailable.' };
  }
}

/**
 * Get groups of duplicate files (by content hash).
 *
 * @param {string} [provider] Optional provider filter
 * @returns {Promise<Array>}
 */
export async function getDuplicates(provider) {
  try {
    const params = provider ? { provider } : {};
    const { data } = await api.get('/api/files/duplicates', { params });
    return data;
  } catch (err) {
    if (isBackendError(err)) throw err;
    return [];
  }
}

/**
 * List files with client-side filtering and sorting.
 * Under the hood this calls POST /api/search with use_ai=false.
 *
 * @param {object}  opts
 * @param {string}  opts.provider  - 'all' or display name ('Google Drive') or key ('google_drive')
 * @param {string}  opts.sort      - 'latest'|'oldest'|'name-asc'|'name-desc'|'size'
 * @param {string}  opts.search    - keyword filter
 * @returns {Promise<object[]>}     Normalized file objects
 */
export async function listFiles({ provider = 'all', sort = 'latest', search = '' } = {}) {
  try {
    const payload = {
      query: search || '*',
      use_ai: false,
      limit: 50,
    };

    if (provider && provider !== 'all') {
      const key = PROVIDER_KEY[provider] || provider;
      payload.providers = [key];
    }

    const { data } = await api.post('/api/search', payload);
    let files = (data.results || []).map(normalizeFile).filter(Boolean);

    // Client-side sorting (backend returns by relevance)
    switch (sort) {
      case 'oldest':
        files.sort((a, b) => new Date(a.created_at || 0) - new Date(b.created_at || 0));
        break;
      case 'name-asc':
        files.sort((a, b) => a.name.localeCompare(b.name));
        break;
      case 'name-desc':
        files.sort((a, b) => b.name.localeCompare(a.name));
        break;
      case 'size':
        files.sort((a, b) => (b.sizeBytes || 0) - (a.sizeBytes || 0));
        break;
      default: // latest
        files.sort((a, b) => new Date(b.modified_at || 0) - new Date(a.modified_at || 0));
    }

    return files;
  } catch (err) {
    if (isBackendError(err)) throw err;
    if (isDemoUser()) {
      console.warn('[FileService] Backend offline, falling back to mock data for demo user');
      const { getFiles } = await import('../data/mockData');
      return getFiles({ provider, sort, search });
    }
    return [];
  }
}

/**
 * Get recently modified / accessed files.
 *
 * @param {number} [limit=10]
 * @returns {Promise<object[]>}
 */
export async function getRecentFiles(limit = 10) {
  try {
    const { data } = await api.post('/api/search', {
      query: '*',
      use_ai: false,
      limit,
    });
    const files = (data.results || []).map(normalizeFile).filter(Boolean);
    // Sort by most recently modified
    files.sort((a, b) => new Date(b.modified_at || 0) - new Date(a.modified_at || 0));
    return files;
  } catch {
    if (isDemoUser()) {
      console.warn('[FileService] Backend offline, falling back to mock recent files for demo user');
      const { getRecentFiles: mockRecent } = await import('../data/mockData');
      return mockRecent();
    }
    return [];
  }
}
