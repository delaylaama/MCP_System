/**
 * Search service — bridges the React UI to the FastAPI search pipeline:
 *   User Query → AI Intent → MCP Client → Provider Adapters → Ranked Results
 *
 * Also exports normalizeFile() used by other services to convert backend
 * FileRecord schemas into the shape the existing React components expect.
 *
 * Backend contract:
 *   POST   /api/search          → SearchResponse
 *   GET    /api/search/history   → SearchHistoryResponse[]
 *   DELETE /api/search/history   → {message, count}
 */

import api, { isBackendError, isDemoUser } from './api';
import { searchFiles as mockSearch } from '../data/mockData';

// ── Display-name mapping for provider keys ──
const PROVIDER_DISPLAY = {
  google_drive: 'Google Drive',
  onedrive: 'OneDrive',
  dropbox: 'Dropbox',
  local: 'Local',
};

// ── Helpers ──

/** Human-readable file size string from byte count. */
export function formatFileSize(bytes) {
  if (bytes == null || bytes === 0) return '0 B';
  const units = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(1024));
  return `${(bytes / Math.pow(1024, i)).toFixed(i > 0 ? 1 : 0)} ${units[i]}`;
}

/** Format ISO datetime to "Month DD, YYYY". */
export function formatDate(iso) {
  if (!iso) return '';
  return new Date(iso).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: '2-digit',
  });
}

/**
 * Convert a backend FileRecord into the shape consumed by existing React
 * components (FileCard, SearchResult, FileDetails, etc.).
 *
 * Backend FileRecord fields:
 *   id, provider, provider_file_id, name, path, mime_type, extension,
 *   size (int bytes), created_at, modified_at, web_url, downloadable,
 *   is_folder, content_available, content_hash, score, score_breakdown, metadata
 *
 * Frontend expected shape:
 *   id, name, provider (display), type (extension), size (string),
 *   modified (string), created (string), path, favorite, tags, aiSummary, etc.
 */
export function normalizeFile(record) {
  if (!record) return null;

  const ext =
    (record.extension || '').replace(/^\./, '') ||
    record.name?.split('.').pop()?.toLowerCase() ||
    '';

  return {
    // Core identifiers
    id: record.id,
    provider_file_id: record.provider_file_id,
    providerKey: record.provider,                         // raw key for API calls
    provider: PROVIDER_DISPLAY[record.provider] || record.provider, // display name

    // File metadata
    name: record.name || 'Untitled',
    type: ext.toLowerCase(),
    size: typeof record.size === 'number' ? formatFileSize(record.size) : (record.size || '0 B'),
    sizeBytes: typeof record.size === 'number' ? record.size : 0,
    path: record.path || '',
    mime_type: record.mime_type,

    // Dates
    modified: formatDate(record.modified_at),
    created: formatDate(record.created_at),
    modified_at: record.modified_at,
    created_at: record.created_at,

    // Links & capabilities
    web_url: record.web_url,
    downloadable: record.downloadable ?? true,
    content_available: record.content_available ?? false,

    // Scoring (from ranking engine)
    score: record.score,
    score_breakdown: record.score_breakdown,
    relevance_reason: record.metadata?.relevance_reason || (record.score ? `Match Score: ${(record.score * 100).toFixed(0)}%` : ''),
    matched_terms: record.metadata?.matched_terms || [],

    // Client-managed fields (not from backend yet)
    favorite: false,
    lastOpened: '',
    tags: record.metadata?.tags || [],
    aiSummary: record.metadata?.ai_summary || '',

    // Hash for duplicate detection
    content_hash: record.content_hash,
  };
}

// ── API Functions ──

/**
 * Execute a natural-language or keyword search via the backend AI pipeline.
 *
 * @param {string} query   - Search query text
 * @param {object} options - { providers, fileType, useAI, limit }
 * @returns {Promise<{files: object[], message: string, total: number, intent: object}>}
 */
export async function search(query, options = {}) {
  try {
    const savedMode = localStorage.getItem('ai_fm_search_mode') || 'hybrid_ai';
    const effectiveMode = options.searchMode || savedMode;
    const useAI = options.useAI !== undefined ? options.useAI : (effectiveMode !== 'keyword');

    const { data } = await api.post('/api/search', {
      query,
      providers: options.providers || null,
      file_type: options.fileType || null,
      use_ai: useAI,
      limit: options.limit || 20,
    });

    const files = (data.results || []).map(normalizeFile).filter(Boolean);

    return {
      files,
      message:
        data.ai_summary ||
        `Found ${data.total_results} result${data.total_results !== 1 ? 's' : ''} for "${query}".`,
      total: data.total_results,
      intent: data.interpreted_intent,
      rankingWeights: data.ranking_weights_used,
    };
  } catch (err) {
    if (isBackendError(err)) throw err;
    if (isDemoUser()) {
      console.warn('[SearchService] Backend offline, falling back to mock search for demo user');
      return mockSearch(query);
    }
    return { files: [], message: `No files found matching "${query}".`, total: 0 };
  }
}

/**
 * Retrieve the user's search history.
 * @returns {Promise<Array>}
 */
export async function getSearchHistory() {
  try {
    const { data } = await api.get('/api/search/history');
    return data;
  } catch (err) {
    if (isBackendError(err)) throw err;
    return [];
  }
}

/**
 * Clear the user's search history.
 * @returns {Promise<{message: string, count: number}>}
 */
export async function clearSearchHistory() {
  try {
    const { data } = await api.delete('/api/search/history');
    return data;
  } catch (err) {
    if (isBackendError(err)) throw err;
    return { message: 'History cleared.', count: 0 };
  }
}
