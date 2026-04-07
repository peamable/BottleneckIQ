import React, { useEffect, useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { Activity, BarChart3, Search } from 'lucide-react';
import { useAuth } from '../context/auth_context.jsx';

const errorMessages = {
  'auth/email-already-in-use': 'That email is already registered. Log in instead or use a different email.',
  'auth/invalid-credential': 'Incorrect email or password.',
  'auth/invalid-email': 'Enter a valid email address.',
  'auth/missing-password': 'Enter your password to continue.',
  'auth/too-many-requests': 'Too many attempts. Wait a moment and try again.',
  'auth/weak-password': 'Use a stronger password with at least 6 characters.',
};

const AuthPage = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, authLoading, logIn, signUp } = useAuth();
  const [mode, setMode] = useState('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const destination = '/view_metrics';

  useEffect(() => {
    if (!authLoading && user) {
      navigate(destination, { replace: true });
    }
  }, [authLoading, destination, navigate, user]);

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError('');

    if (mode === 'signup' && password !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }

    setIsSubmitting(true);

    try {
      if (mode === 'signup') {
        await signUp(email, password);
      } else {
        await logIn(email, password);
      }
    } catch (err) {
      setError(errorMessages[err.code] || 'Authentication failed. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-card">
        <section className="auth-copy-panel">
          <Link to="/" className="auth-brand">
            <div className="auth-brand-icon">
              <Activity size={24} color="#ffffff" />
            </div>
            <span className="auth-brand-text">
              Bottleneck<span className="auth-brand-accent">IQ</span>
            </span>
          </Link>

          <p className="auth-eyebrow">Welcome</p>
          <div className="auth-hero-row">
            <div className="auth-hero-illustration" aria-hidden="true">
              <div className="auth-hero-search-shell">
                <div className="auth-hero-chart-core">
                  <BarChart3 size={72} strokeWidth={2.3} />
                </div>
                <Search size={164} strokeWidth={2.2} />
              </div>
            </div>
            <h1>Your Bottleneck Finder</h1>
          </div>
        </section>

        <section className="auth-form-panel">
          <div className="auth-form-copy">
            <h2>{mode === 'signup' ? 'Create your account' : 'Welcome back'}</h2>
            <p>
              {mode === 'signup'
                ? 'Please enter your details'
                : 'Please enter your details.'}
            </p>
          </div>

          <form className="auth-form" onSubmit={handleSubmit}>
            <label className="auth-field">
              <span>Email</span>
              <input
                type="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                placeholder="analyst@hospital.org"
                autoComplete="email"
                required
              />
            </label>

            <label className="auth-field">
              <span>Password</span>
              <input
                type="password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                placeholder="Enter your password"
                autoComplete={mode === 'signup' ? 'new-password' : 'current-password'}
                required
              />
            </label>

            {mode === 'signup' && (
              <label className="auth-field">
                <span>Confirm password</span>
                <input
                  type="password"
                  value={confirmPassword}
                  onChange={(event) => setConfirmPassword(event.target.value)}
                  placeholder="Repeat your password"
                  autoComplete="new-password"
                  required
                />
              </label>
            )}

            {error && (
              <div className="auth-error" role="alert" aria-live="polite">
                {error}
              </div>
            )}

            <button type="submit" className="auth-submit-button" disabled={isSubmitting}>
              {isSubmitting
                ? (mode === 'signup' ? 'Creating account...' : 'Signing in...')
                : (mode === 'signup' ? 'Sign Up' : 'Log In')}
            </button>
          </form>

          <p className="auth-switch-copy">
            {mode === 'signup' ? 'Already have an account?' : 'New to BottleneckIQ?'}
            <button
              type="button"
              className="auth-inline-toggle"
              onClick={() => {
                setMode(mode === 'signup' ? 'login' : 'signup');
                setError('');
              }}
            >
              {mode === 'signup' ? 'Log in' : 'Sign Up'}
            </button>
          </p>
        </section>
      </div>
    </div>
  );
};

export default AuthPage;
