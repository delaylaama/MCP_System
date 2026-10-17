import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { FILE_TYPES } from '../data/mockData';
import { downloadFile } from '../services/fileService';
import ProviderIcon from './ProviderIcon';
import toast from 'react-hot-toast';

export default function SearchResult({ file, showRelevance = false }) {
  const navigate = useNavigate();
  const [downloading, setDownloading] = useState(false);
  const [localExpanded, setLocalExpanded] = useState(false);

  const isRelevanceVisible = showRelevance || localExpanded;

  const fileType = FILE_TYPES[file.type] || {
    label: file.type?.toUpperCase() || 'FILE',
    icon: 'bi-file-earmark',
  };

  const handleDownload = async (e) => {
    e.stopPropagation();
    setDownloading(true);
    toast.success(`Starting download for ${file.name}...`);
    try {
      const res = await downloadFile(file.id);
      if (res.error) toast.error(res.error);
    } catch {
      toast.error('Download failed.');
    } finally {
      setDownloading(false);
    }
  };

  const toggleLocalRelevance = (e) => {
    e.stopPropagation();
    setLocalExpanded(!localExpanded);
  };

  const scorePct = file.score != null ? Math.round(file.score * 100) : null;
  const scoreColor =
    scorePct >= 75 ? '#34d399' : scorePct >= 50 ? '#60a5fa' : scorePct >= 30 ? '#f59e0b' : '#9ca3af';

  return (
    <div
      className="card-base"
      style={{
        padding: '16px 20px',
        cursor: 'pointer',
        transition: 'all 0.18s ease',
        border: isRelevanceVisible ? '1px solid rgba(59, 130, 246, 0.35)' : '1px solid var(--color-border)',
        boxShadow: isRelevanceVisible ? '0 4px 16px rgba(0, 0, 0, 0.25)' : 'none',
        borderRadius: 10,
        marginBottom: 10,
      }}
      onClick={() => navigate(`/file/${file.id}`)}
    >
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: 14 }}>
        {/* Type badge */}
        <div className={`file-type-badge ${file.type}`} style={{ marginTop: 2 }}>
          {fileType.label}
        </div>

        {/* Main Info */}
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap', marginBottom: 4 }}>
            <div style={{ fontSize: 14.5, fontWeight: 600, color: 'var(--color-text-primary)' }}>
              {file.name}
            </div>

            {/* Match score badge */}
            {scorePct != null && (
              <span
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: 5,
                  padding: '2px 8px',
                  borderRadius: 12,
                  fontSize: 11,
                  fontWeight: 600,
                  background: 'rgba(255, 255, 255, 0.05)',
                  border: `1px solid ${scoreColor}40`,
                  color: scoreColor,
                }}
                title="AI Relevance Score"
              >
                <i className="bi bi-stars" style={{ fontSize: 10 }} />
                {scorePct}% Match
              </span>
            )}
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
            <ProviderIcon provider={file.provider} showLabel />
            <span style={{ fontSize: 11.5, color: 'var(--color-text-muted)' }}>
              <i className="bi bi-clock" style={{ marginRight: 4 }} />
              Modified {file.modified}
            </span>
            <span style={{ fontSize: 11.5, color: 'var(--color-text-muted)' }}>{file.size}</span>
          </div>

          <div style={{ fontSize: 11.5, color: 'var(--color-text-muted)', marginTop: 4 }}>
            <i className="bi bi-folder" style={{ marginRight: 5 }} />
            {file.path}
          </div>
        </div>

        {/* Actions */}
        <div
          style={{ display: 'flex', gap: 8, flexShrink: 0, alignItems: 'center' }}
          onClick={(e) => e.stopPropagation()}
        >
          {/* Individual Why Relevant toggle */}
          <button
            className="btn-outline-custom"
            style={{
              fontSize: 11.5,
              padding: '6px 10px',
              color: isRelevanceVisible ? '#60a5fa' : 'var(--color-text-muted)',
              borderColor: isRelevanceVisible ? 'rgba(59, 130, 246, 0.5)' : 'var(--color-border)',
              background: isRelevanceVisible ? 'rgba(59, 130, 246, 0.1)' : 'transparent',
            }}
            onClick={toggleLocalRelevance}
            title={isRelevanceVisible ? 'Hide relevance insights' : 'Why is this file relevant?'}
          >
            <i className="bi bi-info-circle" /> {isRelevanceVisible ? 'Hide Why' : 'Why?'}
          </button>

          <button
            className="btn-outline-custom"
            style={{ fontSize: 12, padding: '6px 12px' }}
            onClick={() => navigate(`/file/${file.id}`)}
          >
            <i className="bi bi-eye" /> Open
          </button>

          <button
            className="btn-outline-custom"
            style={{ fontSize: 12, padding: '6px 12px' }}
            onClick={handleDownload}
            disabled={downloading}
          >
            <i className="bi bi-download" /> {downloading ? '...' : 'Download'}
          </button>
        </div>
      </div>

      {/* Relevance Details Panel (Visible when toggled) */}
      {isRelevanceVisible && (
        <div
          style={{
            marginTop: 14,
            padding: '12px 16px',
            background: 'var(--color-surface-2, rgba(255, 255, 255, 0.03))',
            border: '1px solid rgba(59, 130, 246, 0.25)',
            borderRadius: 8,
            animation: 'fadeIn 0.2s ease',
          }}
          onClick={(e) => e.stopPropagation()}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
            <div style={{ fontSize: 12, fontWeight: 700, color: '#60a5fa', display: 'flex', alignItems: 'center', gap: 6 }}>
              <i className="bi bi-stars" />
              <span>AI Search Relevance Explanation</span>
            </div>
            {scorePct != null && (
              <span style={{ fontSize: 11, fontWeight: 600, color: scoreColor }}>
                Overall Relevance: {scorePct}%
              </span>
            )}
          </div>

          {/* Natural language reason */}
          <div style={{ fontSize: 12.5, color: 'var(--color-text-primary)', marginBottom: 10, lineHeight: 1.5 }}>
            <strong style={{ color: 'var(--color-text-secondary)', marginRight: 6 }}>Reason:</strong>
            {file.relevance_reason || 'Matched query concepts and search terms.'}
          </div>

          {/* Score breakdown metrics */}
          {file.score_breakdown && (
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(105px, 1fr))',
                gap: 8,
                padding: '10px 12px',
                background: 'rgba(0, 0, 0, 0.2)',
                borderRadius: 6,
                border: '1px solid var(--color-border-light)',
              }}
            >
              <div>
                <div style={{ fontSize: 10, color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                  Keyword Match
                </div>
                <div style={{ fontSize: 13, fontWeight: 700, color: '#38bdf8' }}>
                  {Math.round((file.score_breakdown.keyword_score || 0) * 100)}%
                </div>
              </div>

              <div>
                <div style={{ fontSize: 10, color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                  Semantic AI
                </div>
                <div style={{ fontSize: 13, fontWeight: 700, color: '#a78bfa' }}>
                  {Math.round((file.score_breakdown.semantic_score || 0) * 100)}%
                </div>
              </div>

              <div>
                <div style={{ fontSize: 10, color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                  Exact Match
                </div>
                <div style={{ fontSize: 13, fontWeight: 700, color: '#34d399' }}>
                  {Math.round((file.score_breakdown.exact_match_score || 0) * 100)}%
                </div>
              </div>

              <div>
                <div style={{ fontSize: 10, color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                  Recency Boost
                </div>
                <div style={{ fontSize: 13, fontWeight: 700, color: '#f59e0b' }}>
                  {Math.round((file.score_breakdown.recency_score || 0) * 100)}%
                </div>
              </div>
            </div>
          )}

          {/* Matched search terms pill tags */}
          {file.matched_terms && file.matched_terms.length > 0 && (
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginTop: 10, flexWrap: 'wrap' }}>
              <span style={{ fontSize: 11, color: 'var(--color-text-muted)' }}>Matched Query Terms:</span>
              {file.matched_terms.map((term, i) => (
                <span
                  key={i}
                  style={{
                    fontSize: 11,
                    padding: '2px 8px',
                    borderRadius: 4,
                    background: 'rgba(59, 130, 246, 0.15)',
                    border: '1px solid rgba(59, 130, 246, 0.3)',
                    color: '#93c5fd',
                    fontWeight: 500,
                  }}
                >
                  {term}
                </span>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
