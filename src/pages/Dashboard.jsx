import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useApp } from '../context/AppContext';
import { search as apiSearch } from '../services/searchService';
import { getRecentFiles } from '../services/fileService';
import { listProviders } from '../services/providerService';
import { PROVIDERS, mockStorageProviders, mockFiles } from '../data/mockData';
import FileCard from '../components/FileCard';
import toast from 'react-hot-toast';

const suggestions = [
  'Find my latest resume',
  'Show invoices from June',
  'Find my internship documents',
  'Show files modified last week',
];

const providerIcons = {
  [PROVIDERS.GOOGLE_DRIVE]: { icon: 'bi-google', color: '#4285f4', bg: 'rgba(66,133,244,0.1)' },
  [PROVIDERS.ONEDRIVE]: { icon: 'bi-microsoft', color: '#0078d4', bg: 'rgba(0,120,212,0.1)' },
  'Microsoft OneDrive': { icon: 'bi-microsoft', color: '#0078d4', bg: 'rgba(0,120,212,0.1)' },
  [PROVIDERS.DROPBOX]: { icon: 'bi-dropbox', color: '#0061ff', bg: 'rgba(0,97,255,0.1)' },
  'Dropbox': { icon: 'bi-dropbox', color: '#0061ff', bg: 'rgba(0,97,255,0.1)' },
  'Local': { icon: 'bi-hdd', color: '#374151', bg: 'rgba(55,65,81,0.08)' },
  'Local Storage': { icon: 'bi-hdd', color: '#374151', bg: 'rgba(55,65,81,0.08)' },
  'Local Files': { icon: 'bi-hdd', color: '#374151', bg: 'rgba(55,65,81,0.08)' },
};

export default function Dashboard() {
  const { user, getGreeting } = useApp();
  const navigate = useNavigate();
  const isDemo = user?.email === 'meens@example.com';
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState(null);
  const [searching, setSearching] = useState(false);
  const [providers, setProviders] = useState(mockStorageProviders);
  const [recentFiles, setRecentFiles] = useState(isDemo ? mockFiles.slice(0, 4) : []);

  useEffect(() => {
    let isMounted = true;
    listProviders()
      .then((data) => {
        if (isMounted && data && data.length > 0) setProviders(data);
      })
      .catch((err) => {
        console.warn('Dashboard failed to load providers:', err);
      });
    getRecentFiles(4).then((data) => {
      if (isMounted) setRecentFiles(data || []);
    });
    return () => { isMounted = false; };
  }, [user?.email]);

  const handleSearch = async (q) => {
    const query = q || searchQuery;
    if (!query.trim()) return;
    setSearching(true);
    try {
      const result = await apiSearch(query);
      setSearchResults(result);
    } finally {
      setSearching(false);
    }
  };

  const handleSuggestionClick = (s) => {
    setSearchQuery(s);
    handleSearch(s);
  };

  const handleFullSearch = () => {
    if (searchQuery.trim()) {
      navigate(`/ai-search?q=${encodeURIComponent(searchQuery.trim())}`);
    } else {
      navigate('/ai-search');
    }
  };

  return (
    <div>
      {/* Greeting */}
      <div className="greeting-section">
        <h1 className="greeting-title">{getGreeting()}, {user?.name} 👋</h1>
        <p className="greeting-sub">Search and manage all your files from one intelligent workspace.</p>
      </div>

      {/* Storage Summary */}
      <div className="stats-row">
        {providers.map((p) => {
          const conf = providerIcons[p.name] || { icon: 'bi-cloud', color: '#6b7280', bg: 'rgba(107,114,128,0.1)' };
          return (
            <div key={p.id} className="card-base stat-card" style={{ cursor: 'pointer' }} onClick={() => navigate('/storage')}>
              <div className="stat-card-icon" style={{ background: conf.bg }}>
                <i className={`bi ${conf.icon}`} style={{ color: conf.color }} />
              </div>
              <div className="stat-card-value">{p.fileCount}</div>
              <div className="stat-card-label">{p.name}</div>
              <div style={{ fontSize: 11.5, color: 'var(--color-text-secondary)', margin: '2px 0 6px' }}>
                {p.connected ? `${p.usedStorage} of ${p.totalStorage}` : 'Not connected'}
              </div>
              <div className={`stat-card-status ${p.connected ? 'connected' : ''}`}>
                {p.connected ? (
                  <><i className="bi bi-check-circle-fill" /> Connected</>
                ) : (
                  <><i className="bi bi-x-circle" style={{ color: 'var(--color-text-muted)' }} /> Disconnected</>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* AI Search Card */}
      <div className="card-base ai-search-card">
        <div className="ai-search-label">
          <i className="bi bi-stars" /> AI-Powered Search
        </div>
        <div className="ai-search-heading">Ask anything about your files</div>

        <div className="ai-search-input-wrap">
          <input
            type="text"
            className="ai-search-input"
            placeholder="Find the latest invoice from June..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
          />
          <button
            className="ai-search-btn"
            onClick={handleFullSearch}
          >
            <i className="bi bi-stars" />
            Search
          </button>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 14, flexWrap: 'wrap' }}>
          <span style={{ fontSize: 12, color: 'var(--color-text-muted)' }}>Try asking:</span>
          <div className="ai-suggestions">
            {suggestions.map((s) => (
              <button
                key={s}
                className="ai-suggestion-chip"
                onClick={() => handleSuggestionClick(s)}
              >
                {s}
              </button>
            ))}
          </div>
        </div>

        {/* Quick search results preview */}
        {searching && (
          <div style={{ marginTop: 20, display: 'flex', alignItems: 'center', gap: 10 }}>
            <div className="spinner" style={{ width: 18, height: 18 }} />
            <span style={{ fontSize: 13, color: 'var(--color-text-muted)' }}>AI is searching your files...</span>
          </div>
        )}
        {searchResults && !searching && (
          <div style={{ marginTop: 20 }}>
            <div className="divider" />
            <div style={{ fontSize: 13, color: 'var(--color-text-secondary)', marginBottom: 12, display: 'flex', alignItems: 'center', gap: 8 }}>
              <i className="bi bi-cpu" style={{ color: 'var(--color-primary)' }} />
              {searchResults.message}
              <button
                className="btn-outline-custom"
                style={{ marginLeft: 'auto', fontSize: 12, padding: '5px 12px' }}
                onClick={handleFullSearch}
              >
                Open AI Search <i className="bi bi-arrow-right" />
              </button>
            </div>
            {searchResults.files.length > 0 && (
              <div className="grid-2">
                {searchResults.files.slice(0, 4).map((f) => (
                  <FileCard key={f.id} file={f} view="grid" />
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* MCP Architecture */}
      <div className="card-base mcp-arch">
        <div className="flex-between" style={{ marginBottom: 20 }}>
          <div>
            <div className="mcp-arch-title">
              <i className="bi bi-diagram-3" style={{ marginRight: 8, color: 'var(--color-primary)' }} />
              How It Works — MCP Architecture
            </div>
            <div className="mcp-arch-desc">
              Powered by Model Context Protocol (MCP) — the AI bridges your files across all storage providers.
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', gap: 40, alignItems: 'flex-start', flexWrap: 'wrap' }}>
          {/* Flow diagram */}
          <div style={{ flex: '0 0 auto' }}>
            <div className="mcp-flow">
              <div className="mcp-node primary">
                <i className="bi bi-person-circle" />
                You
              </div>
              <div className="mcp-connector" />
              <div className="mcp-node primary">
                <i className="bi bi-window" />
                React Frontend
              </div>
              <div className="mcp-connector" />
              <div className="mcp-node primary">
                <i className="bi bi-cpu" />
                AI / LLM
              </div>
              <div className="mcp-connector" />
              <div className="mcp-node" style={{ background: 'var(--color-surface-2)', color: 'var(--color-text-secondary)' }}>
                <i className="bi bi-arrow-left-right" />
                MCP Client
              </div>
              <div className="mcp-connector" />
              <div className="mcp-node" style={{ background: 'var(--color-surface-2)', color: 'var(--color-text-secondary)' }}>
                <i className="bi bi-server" />
                MCP Server
              </div>
              <div className="mcp-connector" />
              <div className="mcp-providers-row">
                {[
                  { icon: 'bi-google', label: 'Google Drive', color: '#4285f4' },
                  { icon: 'bi-microsoft', label: 'OneDrive', color: '#0078d4' },
                  { icon: 'bi-dropbox', label: 'Dropbox', color: '#0061ff' },
                  { icon: 'bi-hdd', label: 'Local', color: '#374151' },
                ].map((p) => (
                  <div
                    key={p.label}
                    style={{
                      display: 'flex',
                      flexDirection: 'column',
                      alignItems: 'center',
                      gap: 6,
                    }}
                  >
                    <div className="mcp-connector" style={{ height: 20 }} />
                    <div
                      style={{
                        background: 'var(--color-surface-2)',
                        border: '1px solid var(--color-border)',
                        borderRadius: 'var(--radius-md)',
                        padding: '8px 12px',
                        display: 'flex',
                        flexDirection: 'column',
                        alignItems: 'center',
                        gap: 4,
                        minWidth: 70,
                      }}
                    >
                      <i className={`bi ${p.icon}`} style={{ fontSize: 18, color: p.color }} />
                      <span style={{ fontSize: 10, fontWeight: 600, color: 'var(--color-text-secondary)' }}>
                        {p.label}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Explanation */}
          <div style={{ flex: 1, minWidth: 200 }}>
            {[
              { icon: 'bi-chat-dots', title: 'Natural Language Query', desc: 'You type a question like "Find my June invoice" in plain English.', color: 'var(--color-primary)' },
              { icon: 'bi-cpu', title: 'AI Processing', desc: 'The LLM understands your intent and instructs the MCP client what to search for.', color: '#7c3aed' },
              { icon: 'bi-arrow-left-right', title: 'MCP Protocol', desc: 'The MCP client communicates with MCP servers using a standardized protocol.', color: '#0ea5e9' },
              { icon: 'bi-cloud-arrow-down', title: 'Multi-Cloud Retrieval', desc: 'Results are fetched simultaneously from Google Drive, OneDrive, Dropbox, and Local storage.', color: '#059669' },
            ].map((step, i) => (
              <div key={i} style={{ display: 'flex', gap: 14, marginBottom: 20 }}>
                <div
                  style={{
                    width: 36,
                    height: 36,
                    borderRadius: 'var(--radius-md)',
                    background: `${step.color}15`,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    flexShrink: 0,
                  }}
                >
                  <i className={`bi ${step.icon}`} style={{ color: step.color, fontSize: 16 }} />
                </div>
                <div>
                  <div style={{ fontSize: 13.5, fontWeight: 600, color: 'var(--color-text-primary)', marginBottom: 3 }}>
                    {step.title}
                  </div>
                  <div style={{ fontSize: 12.5, color: 'var(--color-text-secondary)', lineHeight: 1.5 }}>
                    {step.desc}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Recent Files */}
      <div style={{ marginTop: 0 }}>
        <div className="flex-between" style={{ marginBottom: 16 }}>
          <h2 style={{ fontSize: 16, fontWeight: 700 }}>Recent Files</h2>
          <button className="btn-outline-custom" style={{ fontSize: 12.5 }} onClick={() => navigate('/recent')}>
            View all <i className="bi bi-arrow-right" />
          </button>
        </div>
        {recentFiles.length === 0 ? (
          <div className="card-base" style={{ padding: '30px', textAlign: 'center', color: 'var(--color-text-muted)' }}>
            <i className="bi bi-folder2-open" style={{ fontSize: 32, display: 'block', marginBottom: 10, color: 'var(--color-primary)' }} />
            <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--color-text-primary)' }}>No files indexed yet</div>
            <div style={{ fontSize: 12.5, marginTop: 4 }}>Go to Storage to verify your cloud connection, or use AI Search above.</div>
          </div>
        ) : (
          <div className="grid-2">
            {recentFiles.map((f) => (
              <FileCard key={f.id} file={f} view="grid" />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
