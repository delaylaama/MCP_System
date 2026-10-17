import React from 'react';
import Sidebar from '../components/Sidebar';
import Navbar from '../components/Navbar';
import { useApp } from '../context/AppContext';

export default function DashboardLayout({ children }) {
  const { sidebarOpen } = useApp();

  return (
    <div className="app-layout">
      <Sidebar />
      <div className={`main-content ${!sidebarOpen ? '' : ''}`}>
        <Navbar />
        <main className="page-content">{children}</main>
      </div>
    </div>
  );
}
