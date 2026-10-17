import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useApp } from '../context/AppContext';
import { login as apiLogin } from '../services/authService';
import toast from 'react-hot-toast';

export default function Login() {
  const { login } = useApp();
  const navigate = useNavigate();

  const [form, setForm] = useState({ email: '', password: '' });
  const [showPassword, setShowPassword] = useState(false);
  const [remember, setRemember] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
    if (error) setError('');
  };

  const validate = () => {
    if (!form.email.trim()) return 'Email is required.';
    if (!/\S+@\S+\.\S+/.test(form.email)) return 'Please enter a valid email address.';
    if (!form.password) return 'Password is required.';
    if (form.password.length < 6) return 'Password must be at least 6 characters.';
    return null;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const validationError = validate();
    if (validationError) { setError(validationError); return; }

    setLoading(true);
    try {
      const result = await apiLogin(form.email, form.password);
      if (result.success) {
        login(result.user, result.token);
        toast.success(`Welcome back, ${result.user.name}! 👋`);
        navigate('/dashboard');
      } else {
        setError(result.error || 'Invalid credentials.');
      }
    } catch {
      setError('Something went wrong. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  // Demo login shortcut
  const handleDemoLogin = () => {
    setForm({ email: 'meens@example.com', password: 'password123' });
  };

  return (
    <div className="auth-page">
      <div className="auth-card">
        {/* Logo */}
        <div className="auth-logo">
          <div className="auth-logo-icon">
            <i className="bi bi-cpu" />
          </div>
          <div>
            <div className="auth-logo-text">AI File Manager</div>
            <div style={{ fontSize: 11, color: 'var(--color-text-muted)' }}>Universal MCP Platform</div>
          </div>
        </div>

        <h1 className="auth-title">Welcome back</h1>
        <p className="auth-subtitle">Your files. One intelligent workspace.</p>

        {/* Error */}
        {error && (
          <div className="auth-error">
            <i className="bi bi-exclamation-circle-fill" />
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} noValidate>
          {/* Email */}
          <div className="auth-form-group">
            <label className="form-label-custom" htmlFor="login-email">Email address</label>
            <div className="input-group-custom">
              <i className="bi bi-envelope input-icon" />
              <input
                id="login-email"
                type="email"
                name="email"
                className="form-control-custom"
                placeholder="you@example.com"
                value={form.email}
                onChange={handleChange}
                autoComplete="email"
              />
            </div>
          </div>

          {/* Password */}
          <div className="auth-form-group">
            <div className="flex-between" style={{ marginBottom: 6 }}>
              <label className="form-label-custom" style={{ margin: 0 }} htmlFor="login-password">Password</label>
              <a href="#" style={{ fontSize: 12.5 }} onClick={(e) => e.preventDefault()}>Forgot password?</a>
            </div>
            <div className="input-group-custom">
              <i className="bi bi-lock input-icon" />
              <input
                id="login-password"
                type={showPassword ? 'text' : 'password'}
                name="password"
                className="form-control-custom"
                placeholder="Enter your password"
                value={form.password}
                onChange={handleChange}
                autoComplete="current-password"
              />
              <i
                className={`bi ${showPassword ? 'bi-eye-slash' : 'bi-eye'} input-icon-right`}
                onClick={() => setShowPassword(!showPassword)}
                title={showPassword ? 'Hide password' : 'Show password'}
              />
            </div>
          </div>

          {/* Remember me */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 20 }}>
            <input
              type="checkbox"
              id="remember"
              checked={remember}
              onChange={(e) => setRemember(e.target.checked)}
              style={{ width: 15, height: 15, accentColor: 'var(--color-primary)', cursor: 'pointer' }}
            />
            <label htmlFor="remember" style={{ fontSize: 13, color: 'var(--color-text-secondary)', cursor: 'pointer' }}>
              Remember me
            </label>
          </div>

          {/* Submit */}
          <button
            type="submit"
            className="btn-primary-custom"
            style={{ width: '100%', justifyContent: 'center', padding: '12px 24px', fontSize: 14 }}
            disabled={loading}
          >
            {loading ? (
              <><div className="spinner" style={{ width: 16, height: 16, borderWidth: 2, borderColor: 'rgba(255,255,255,0.3)', borderTopColor: 'white' }} /> Signing in...</>
            ) : (
              <><i className="bi bi-box-arrow-in-right" /> Sign In</>
            )}
          </button>
        </form>

        {/* Demo shortcut */}
        <button
          className="btn-outline-custom"
          style={{ width: '100%', justifyContent: 'center', marginTop: 10, fontSize: 13 }}
          onClick={handleDemoLogin}
          type="button"
        >
          <i className="bi bi-lightning" /> Fill demo credentials
        </button>

        <p className="auth-footer-text">
          Don't have an account?{' '}
          <Link to="/register">Create account</Link>
        </p>
      </div>
    </div>
  );
}
