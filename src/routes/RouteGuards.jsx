import React from 'react';
import { Navigate, Outlet } from 'react-router-dom';
import { useApp } from '../context/AppContext';
import DashboardLayout from '../layouts/DashboardLayout';

export function PrivateRoute() {
  const { user } = useApp();
  if (!user) return <Navigate to="/login" replace />;
  return (
    <DashboardLayout>
      <Outlet />
    </DashboardLayout>
  );
}

export function PublicRoute() {
  const { user } = useApp();
  if (user) return <Navigate to="/dashboard" replace />;
  return <Outlet />;
}
