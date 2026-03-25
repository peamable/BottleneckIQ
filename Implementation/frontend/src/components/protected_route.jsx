import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/auth_context.jsx';

const ProtectedRoute = ({ children }) => {
  const location = useLocation();
  const { user, authLoading } = useAuth();

  if (authLoading) {
    return (
      <div className="auth-route-loading">
        <div className="auth-route-loading-card">
          <h2>Checking your session</h2>
          <p>Hold on while BottleneckIQ verifies your sign-in.</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/auth" replace state={{ from: location }} />;
  }

  return children;
};

export default ProtectedRoute;
