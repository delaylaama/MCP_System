import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { PrivateRoute, PublicRoute } from './RouteGuards';

import Login from '../pages/Login';
import Register from '../pages/Register';
import Dashboard from '../pages/Dashboard';
import AISearch from '../pages/AISearch';
import Files from '../pages/Files';
import Storage from '../pages/Storage';
import Recent from '../pages/Recent';
import Favorites from '../pages/Favorites';
import FileDetails from '../pages/FileDetails';
import Settings from '../pages/Settings';
import Admin from '../pages/Admin';

export default function AppRoutes() {
  return (
    <Routes>
      {/* Public routes */}
      <Route element={<PublicRoute />}>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
      </Route>

      {/* Protected routes */}
      <Route element={<PrivateRoute />}>
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/ai-search" element={<AISearch />} />
        <Route path="/files" element={<Files />} />
        <Route path="/storage" element={<Storage />} />
        <Route path="/recent" element={<Recent />} />
        <Route path="/favorites" element={<Favorites />} />
        <Route path="/file/:id" element={<FileDetails />} />
        <Route path="/settings" element={<Settings />} />
        <Route path="/admin" element={<Admin />} />
      </Route>

      {/* Redirects */}
      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}
