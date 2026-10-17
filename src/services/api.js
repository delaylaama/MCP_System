/**
 * Central Axios HTTP client for the Universal AI File Manager.
 *
 * - Automatically attaches the JWT Bearer token from localStorage to every request.
 * - Intercepts 401 responses → clears stored credentials → redirects to /login.
 * - Provides a helper to distinguish backend errors from network failures.
 */

import axios from 'axios';

export const TOKEN_KEY = 'ai_file_manager_token';
export const USER_KEY = 'ai_file_manager_user';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// ── Request interceptor: attach JWT ──
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem(TOKEN_KEY);
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error),
);

// ── Response interceptor: handle 401 globally ──
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem(TOKEN_KEY);
      localStorage.removeItem(USER_KEY);
      const path = window.location.pathname;
      if (!path.startsWith('/login') && !path.startsWith('/register')) {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  },
);

/**
 * Returns true when the error is a real backend HTTP response (4xx with JSON payload),
 * as opposed to a network failure or proxy error (502/504/ECONNREFUSED/HTML error page).
 */
export function isBackendError(err) {
  if (!err || !err.response) return false;
  const status = err.response.status;
  // If status is 4xx and response is JSON, it's a genuine FastAPI error
  return status >= 400 && status < 500 && typeof err.response.data === 'object';
}

export function isDemoUser() {
  try {
    const raw = localStorage.getItem(USER_KEY);
    if (!raw) return false;
    const user = JSON.parse(raw);
    return user.email === 'meens@example.com';
  } catch {
    return false;
  }
}

export default api;
