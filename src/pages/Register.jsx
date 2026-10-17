import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { register as apiRegister } from '../services/authService';
import toast from 'react-hot-toast';

export default function Register() {
  const navigate = useNavigate();

  const [form, setForm] = useState({ name: '', email: '', password: '', confirmPassword: '' });
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState({});

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
    if (errors[e.target.name]) setErrors({ ...errors, [e.target.name]: '' });
  };

  const validate = () => {
    const errs = {};
    if (!form.name.trim()) errs.name = 'Full name is required.';
    if (!form.email.trim()) errs.email = 'Email is required.';
    else if (!/\S+@\S+\.\S+/.test(form.email)) errs.email = 'Enter a valid email.';
    if (!form.password) errs.password = 'Password is required.';
    else if (form.password.length < 6) errs.password = 'Password must be at least 6 characters.';
    if (!form.confirmPassword) errs.confirmPassword = 'Please confirm your password.';
    else if (form.password !== form.confirmPassword) errs.confirmPassword = 'Passwords do not match.';
    return errs;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const errs = validate();
    if (Object.keys(errs).length > 0) { setErrors(errs); return; }

    setLoading(true);
    try {
      const result = await apiRegister(form.name, form.email, form.password);
      if (result.success) {
        toast.success('Account created! Please sign in.');
        navigate('/login');
      } else {
        setErrors({ general: result.error });
      }
    } catch {
      setErrors({ general: 'Something went wrong. Please try again.' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-card">
        {/* Logo */}
        <div className="auth-logo">
          <div className="auth-logo-icon"><i className="bi bi-cpu" /></div>
          <div>
            <div className="auth-logo-text">AI File Manager</div>
            <div style={{ fontSize: 11, color: 'var(--color-text-muted)' }}>Universal MCP Platform</div>
          </div>
        </div>

        <h1 className="auth-title">Create account</h1>
        <p className="auth-subtitle">Start managing your files with AI intelligence.</p>

        {errors.general && (
          <div className="auth-error">
            <i className="bi bi-exclamation-circle-fill" /> {errors.general}
          </div>
        )}

        <form onSubmit={handleSubmit} noValidate>
          {/* Full Name */}
          <div className="auth-form-group">
            <label className="form-label-custom" htmlFor="reg-name">Full Name</label>
            <div className="input-group-custom">
              <i className="bi bi-person input-icon" />
              <input
                id="reg-name"
                type="text"
                name="name"
                className="form-control-custom"
                placeholder="Your full name"
                value={form.name}
                onChange={handleChange}
              />
            </div>
            {errors.name && <div style={{ color: 'var(--color-danger)', fontSize: 12, marginTop: 4 }}>{errors.name}</div>}
          </div>

          {/* Email */}
          <div className="auth-form-group">
            <label className="form-label-custom" htmlFor="reg-email">Email address</label>
            <div className="input-group-custom">
              <i className="bi bi-envelope input-icon" />
              <input
                id="reg-email"
                type="email"
                name="email"
                className="form-control-custom"
                placeholder="you@example.com"
                value={form.email}
                onChange={handleChange}
              />
            </div>
            {errors.email && <div style={{ color: 'var(--color-danger)', fontSize: 12, marginTop: 4 }}>{errors.email}</div>}
          </div>

          {/* Password */}
          <div className="auth-form-group">
            <label className="form-label-custom" htmlFor="reg-password">Password</label>
            <div className="input-group-custom">
              <i className="bi bi-lock input-icon" />
              <input
                id="reg-password"
                type={showPassword ? 'text' : 'password'}
                name="password"
                className="form-control-custom"
                placeholder="At least 6 characters"
                value={form.password}
                onChange={handleChange}
              />
              <i
                className={`bi ${showPassword ? 'bi-eye-slash' : 'bi-eye'} input-icon-right`}
                onClick={() => setShowPassword(!showPassword)}
              />
            </div>
            {errors.password && <div style={{ color: 'var(--color-danger)', fontSize: 12, marginTop: 4 }}>{errors.password}</div>}
          </div>

          {/* Confirm Password */}
          <div className="auth-form-group">
            <label className="form-label-custom" htmlFor="reg-confirm">Confirm Password</label>
            <div className="input-group-custom">
              <i className="bi bi-shield-lock input-icon" />
              <input
                id="reg-confirm"
                type={showConfirm ? 'text' : 'password'}
                name="confirmPassword"
                className="form-control-custom"
                placeholder="Repeat your password"
                value={form.confirmPassword}
                onChange={handleChange}
              />
              <i
                className={`bi ${showConfirm ? 'bi-eye-slash' : 'bi-eye'} input-icon-right`}
                onClick={() => setShowConfirm(!showConfirm)}
              />
            </div>
            {errors.confirmPassword && <div style={{ color: 'var(--color-danger)', fontSize: 12, marginTop: 4 }}>{errors.confirmPassword}</div>}
          </div>

          <button
            type="submit"
            className="btn-primary-custom"
            style={{ width: '100%', justifyContent: 'center', padding: '12px 24px', fontSize: 14, marginTop: 4 }}
            disabled={loading}
          >
            {loading ? (
              <><div className="spinner" style={{ width: 16, height: 16, borderWidth: 2, borderColor: 'rgba(255,255,255,0.3)', borderTopColor: 'white' }} /> Creating account...</>
            ) : (
              <><i className="bi bi-person-plus" /> Create Account</>
            )}
          </button>
        </form>

        <p className="auth-footer-text">
          Already have an account?{' '}
          <Link to="/login">Sign in</Link>
        </p>
      </div>
    </div>
  );
}
