/**
 * Authentication service — real backend API calls with graceful mock fallback.
 *
 * Backend contract:
 *   POST /api/auth/login   (OAuth2 form-urlencoded: username + password) → TokenResponse
 *   POST /api/auth/register (JSON: {email, password, full_name})          → UserResponse
 *   GET  /api/auth/me       (Bearer token)                                → UserResponse
 */

import api, { TOKEN_KEY, isBackendError } from './api';
import { loginUser as mockLogin, registerUser as mockRegister } from '../data/mockData';

/**
 * Authenticate user against the FastAPI backend.
 * Falls back to mock if the backend is unreachable.
 *
 * @param {string} email
 * @param {string} password
 * @returns {Promise<{success: boolean, token?: string, user?: object, error?: string}>}
 */
export async function login(email, password) {
  try {
    // FastAPI's OAuth2PasswordRequestForm expects form-urlencoded data
    const params = new URLSearchParams();
    params.append('username', email);
    params.append('password', password);

    const { data } = await api.post('/api/auth/login', params, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });

    // Persist token for future api.js interceptor usage
    localStorage.setItem(TOKEN_KEY, data.access_token);

    return {
      success: true,
      token: data.access_token,
      user: {
        id: data.user.id,
        name: data.user.full_name || data.user.email.split('@')[0],
        fullName: data.user.full_name,
        email: data.user.email,
        isActive: data.user.is_active,
      },
    };
  } catch (err) {
    if (isBackendError(err)) {
      // If demo credentials, allow fallback
      if (email === 'meens@example.com' && password === 'password123') {
        console.warn('[AuthService] Backend rejected demo credentials, falling back to mock login');
        return mockLogin({ email, password });
      }
      return {
        success: false,
        error: err.response.data?.detail || 'Invalid email or password.',
      };
    }
    // Network failure or proxy failure — backend offline
    console.warn('[AuthService] Backend offline or proxy error, falling back to mock login');
    return mockLogin({ email, password });
  }
}

/**
 * Register a new user account.
 *
 * @param {string} name
 * @param {string} email
 * @param {string} password
 * @returns {Promise<{success: boolean, error?: string}>}
 */
export async function register(name, email, password) {
  try {
    await api.post('/api/auth/register', {
      email,
      password,
      full_name: name,
    });
    return { success: true };
  } catch (err) {
    if (isBackendError(err)) {
      return {
        success: false,
        error: err.response.data?.detail || 'Registration failed. Please try again.',
      };
    }
    console.warn('[AuthService] Backend offline, falling back to mock register');
    return mockRegister({ name, email, password });
  }
}

/**
 * Fetch the authenticated user's profile using the stored JWT.
 *
 * @returns {Promise<object>} Normalized user object
 */
export async function getMe() {
  const { data } = await api.get('/api/auth/me');
  return {
    id: data.id,
    name: data.full_name || data.email.split('@')[0],
    fullName: data.full_name,
    email: data.email,
    isActive: data.is_active,
  };
}
