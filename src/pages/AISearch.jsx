import React, { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import AIChat from '../components/AIChat';

export default function AISearch() {
  const [searchParams] = useSearchParams();
  const initialQuery = searchParams.get('q') || '';

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">
          <i className="bi bi-stars" style={{ color: 'var(--color-primary)', marginRight: 10 }} />
          AI Search
        </h1>
        <p className="page-subtitle">
          Ask anything — search across Google Drive, OneDrive, Dropbox, and local files in natural language.
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 280px', gap: 20, alignItems: 'start' }}>
        {/* Chat panel */}
        <div className="card-base" style={{ padding: '24px', minHeight: 600 }}>
          <AIChat key={initialQuery} initialQuery={initialQuery} />
        </div>

        {/* Tips panel */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <div className="card-base" style={{ padding: '20px' }}>
            <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--color-text-primary)', marginBottom: 12, display: 'flex', alignItems: 'center', gap: 8 }}>
              <i className="bi bi-lightbulb" style={{ color: '#f59e0b' }} />
              Search Tips
            </div>
            {[
              'Use natural language like "Find invoices from last month"',
              'Specify file types: "Show all PDF documents"',
              'Search by date: "Files modified this week"',
              'Search by provider: "Files in Dropbox"',
              'Search by content: "Documents about MCP protocol"',
            ].map((tip, i) => (
              <div key={i} style={{ fontSize: 12, color: 'var(--color-text-secondary)', padding: '5px 0', borderBottom: i < 4 ? '1px solid var(--color-border-light)' : 'none', display: 'flex', alignItems: 'flex-start', gap: 8 }}>
                <i className="bi bi-check2" style={{ color: 'var(--color-success)', marginTop: 1, flexShrink: 0 }} />
                {tip}
              </div>
            ))}
          </div>

          <div className="card-base" style={{ padding: '20px' }}>
            <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--color-text-primary)', marginBottom: 12, display: 'flex', alignItems: 'center', gap: 8 }}>
              <i className="bi bi-clock-history" style={{ color: 'var(--color-primary)' }} />
              Quick Searches
            </div>
            {[
              'Find my latest resume',
              'Show invoices from June',
              'Find my internship documents',
              'Show files modified last week',
              'Find project reports',
              'Show my certificates',
            ].map((q) => (
              <button
                key={q}
                style={{
                  display: 'block',
                  width: '100%',
                  textAlign: 'left',
                  background: 'none',
                  border: 'none',
                  padding: '7px 0',
                  fontSize: 12.5,
                  color: 'var(--color-primary)',
                  cursor: 'pointer',
                  borderBottom: '1px solid var(--color-border-light)',
                  fontFamily: 'var(--font-family)',
                }}
                onClick={() => window.location.href = `/ai-search?q=${encodeURIComponent(q)}`}
              >
                <i className="bi bi-search" style={{ marginRight: 6 }} />
                {q}
              </button>
            ))}
          </div>

          <div className="card-base" style={{ padding: '20px', borderLeft: '3px solid var(--color-primary)' }}>
            <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--color-primary)', marginBottom: 8, display: 'flex', alignItems: 'center', gap: 6 }}>
              <i className="bi bi-info-circle" /> About AI Search
            </div>
            <div style={{ fontSize: 12, color: 'var(--color-text-secondary)', lineHeight: 1.6 }}>
              AI Search uses the Model Context Protocol (MCP) to query all your connected storage providers simultaneously and return semantically relevant results.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
