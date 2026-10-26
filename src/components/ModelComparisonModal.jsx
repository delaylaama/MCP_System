import React, { useState, useEffect } from 'react';
import { compareSearchModels } from '../services/searchService';

export default function ModelComparisonModal({ isOpen, onClose, initialQuery = '' }) {
  const [query, setQuery] = useState(initialQuery);
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [selectedFilter, setSelectedFilter] = useState('all'); // 'all', 'speed', 'accuracy'

  useEffect(() => {
    if (isOpen) {
      const q = initialQuery || 'find my final year fees';
      setQuery(q);
      runBenchmark(q);
    }
  }, [isOpen, initialQuery]);

  const runBenchmark = async (benchmarkQuery) => {
    const q = (benchmarkQuery || query).trim();
    if (!q) return;
    setLoading(true);
    setError(null);
    try {
      const res = await compareSearchModels(q, { limitPerModel: 3 });
      setData(res);
    } catch (err) {
      console.error('Benchmark error:', err);
      setError('Failed to benchmark models. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      runBenchmark(query);
    }
  };

  if (!isOpen) return null;

  const models = data?.models || [];
  const speedChampion = models.find((m) => m.model_id === data?.speed_champion_id) || models[0];
  const accuracyChampion = models.find((m) => m.model_id === data?.accuracy_champion_id) || models[1];

  const filteredModels = models.filter((m) => {
    if (selectedFilter === 'speed') return m.model_id === data?.speed_champion_id;
    if (selectedFilter === 'accuracy') return m.model_id === data?.accuracy_champion_id;
    return true;
  });

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 1050,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: 'rgba(5, 10, 20, 0.75)',
        backdropFilter: 'blur(8px)',
        padding: 16,
      }}
      onClick={onClose}
    >
      <div
        style={{
          width: '100%',
          maxWidth: 1140,
          maxHeight: '92vh',
          backgroundColor: '#0f172a',
          borderRadius: 16,
          border: '1px solid rgba(255, 255, 255, 0.12)',
          boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.7), 0 0 40px rgba(59, 130, 246, 0.15)',
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
          color: '#f8fafc',
          fontFamily: 'var(--font-family, system-ui, sans-serif)',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header Bar */}
        <div
          style={{
            padding: '18px 24px',
            borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            background: 'linear-gradient(90deg, rgba(30, 41, 59, 0.9) 0%, rgba(15, 23, 42, 0.9) 100%)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <div
              style={{
                width: 40,
                height: 40,
                borderRadius: 10,
                background: 'linear-gradient(135deg, #3b82f6, #8b5cf6)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                boxShadow: '0 0 15px rgba(99, 102, 241, 0.4)',
              }}
            >
              <i className="bi bi-speedometer2" style={{ fontSize: 20, color: 'white' }} />
            </div>
            <div>
              <div style={{ fontSize: 18, fontWeight: 700, letterSpacing: '-0.02em', display: 'flex', alignItems: 'center', gap: 8 }}>
                <span>5 Open-Source Model Comparison Lab</span>
                <span
                  style={{
                    fontSize: 10.5,
                    padding: '2px 8px',
                    borderRadius: 12,
                    background: 'rgba(59, 130, 246, 0.18)',
                    color: '#60a5fa',
                    border: '1px solid rgba(59, 130, 246, 0.3)',
                    fontWeight: 600,
                  }}
                >
                  Live Multi-Model Benchmark
                </span>
              </div>
              <div style={{ fontSize: 12, color: '#94a3b8', marginTop: 2 }}>
                Real-time latency profiling, semantic match accuracy, architecture trade-offs, and critical model flaws.
              </div>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <button
              onClick={() => {
                const targetUrl = `/models?q=${encodeURIComponent(query || '')}`;
                window.open(targetUrl, '_blank', 'width=1320,height=920,menubar=no,toolbar=no,location=no,status=no');
                onClose();
              }}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: 6,
                background: 'linear-gradient(135deg, rgba(59, 130, 246, 0.2), rgba(139, 92, 246, 0.2))',
                border: '1px solid rgba(99, 102, 241, 0.4)',
                borderRadius: 8,
                padding: '6px 12px',
                color: '#93c5fd',
                fontSize: 12,
                fontWeight: 600,
                cursor: 'pointer',
                transition: 'all 0.2s ease',
              }}
              title="Pop out into a dedicated, separate full benchmark window"
            >
              <i className="bi bi-box-arrow-up-right" style={{ fontSize: 13 }} />
              <span>Open in Separate Window</span>
            </button>

            <button
              onClick={onClose}
              style={{
                background: 'rgba(255, 255, 255, 0.06)',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                borderRadius: '50%',
                width: 34,
                height: 34,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#94a3b8',
                cursor: 'pointer',
                transition: 'all 0.2s ease',
              }}
              title="Close Benchmark (Esc)"
            >
              <i className="bi bi-x-lg" style={{ fontSize: 14 }} />
            </button>
          </div>
        </div>

        {/* Query & Filter Toolbar */}
        <div
          style={{
            padding: '12px 24px',
            background: 'rgba(15, 23, 42, 0.6)',
            borderBottom: '1px solid rgba(255, 255, 255, 0.06)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: 16,
            flexWrap: 'wrap',
          }}
        >
          {/* Query Input */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, flex: 1, minWidth: 280 }}>
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                flex: 1,
                background: 'rgba(30, 41, 59, 0.6)',
                border: '1px solid rgba(255, 255, 255, 0.12)',
                borderRadius: 8,
                padding: '6px 12px',
                gap: 8,
              }}
            >
              <i className="bi bi-search" style={{ color: '#60a5fa', fontSize: 13 }} />
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Enter test query (e.g., 'find my final year fees', 'invoices from june')..."
                style={{
                  background: 'transparent',
                  border: 'none',
                  outline: 'none',
                  color: 'white',
                  fontSize: 13,
                  width: '100%',
                }}
              />
            </div>
            <button
              onClick={() => runBenchmark(query)}
              disabled={loading || !query.trim()}
              style={{
                background: 'linear-gradient(135deg, #2563eb, #3b82f6)',
                border: 'none',
                color: 'white',
                padding: '7px 16px',
                borderRadius: 8,
                fontSize: 12.5,
                fontWeight: 600,
                cursor: loading ? 'not-allowed' : 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: 6,
                boxShadow: '0 2px 8px rgba(37, 99, 235, 0.3)',
              }}
            >
              {loading ? (
                <>
                  <div className="spinner" style={{ width: 14, height: 14, borderWidth: 2 }} />
                  <span>Benchmarking...</span>
                </>
              ) : (
                <>
                  <i className="bi bi-arrow-repeat" />
                  <span>Run Benchmark</span>
                </>
              )}
            </button>
          </div>

          {/* Filter Pills */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            {[
              { id: 'all', label: 'All 5 Models' },
              { id: 'speed', label: '⚡ Speed Winner' },
              { id: 'accuracy', label: '🎯 Accuracy Winner' },
            ].map((f) => (
              <button
                key={f.id}
                onClick={() => setSelectedFilter(f.id)}
                style={{
                  background: selectedFilter === f.id ? 'rgba(59, 130, 246, 0.25)' : 'rgba(255, 255, 255, 0.04)',
                  border: selectedFilter === f.id ? '1px solid rgba(59, 130, 246, 0.5)' : '1px solid rgba(255, 255, 255, 0.08)',
                  color: selectedFilter === f.id ? '#60a5fa' : '#94a3b8',
                  padding: '5px 12px',
                  borderRadius: 20,
                  fontSize: 12,
                  fontWeight: 600,
                  cursor: 'pointer',
                  transition: 'all 0.15s ease',
                }}
              >
                {f.label}
              </button>
            ))}
          </div>
        </div>

        {/* Content Body */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '20px 24px' }}>
          {error && (
            <div
              style={{
                padding: 12,
                borderRadius: 8,
                background: 'rgba(239, 68, 68, 0.15)',
                border: '1px solid rgba(239, 68, 68, 0.3)',
                color: '#fca5a5',
                fontSize: 13,
                marginBottom: 16,
                display: 'flex',
                alignItems: 'center',
                gap: 8,
              }}
            >
              <i className="bi bi-exclamation-triangle" />
              <span>{error}</span>
            </div>
          )}

          {/* Top Level Benchmark Champions Summary */}
          {data && (
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
                gap: 16,
                marginBottom: 24,
              }}
            >
              {/* Speed Champion Card */}
              <div
                style={{
                  background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(6, 78, 59, 0.2) 100%)',
                  border: '1px solid rgba(16, 185, 129, 0.3)',
                  borderRadius: 12,
                  padding: '14px 18px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 14,
                }}
              >
                <div
                  style={{
                    width: 44,
                    height: 44,
                    borderRadius: 10,
                    background: 'rgba(16, 185, 129, 0.2)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: '#34d399',
                    fontSize: 22,
                  }}
                >
                  <i className="bi bi-lightning-charge-fill" />
                </div>
                <div>
                  <div style={{ fontSize: 11, fontWeight: 700, color: '#34d399', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                    Speed Champion (Lowest Latency)
                  </div>
                  <div style={{ fontSize: 15, fontWeight: 700, color: 'white', marginTop: 1 }}>
                    {speedChampion?.model_name.split('/').pop()}
                  </div>
                  <div style={{ fontSize: 12, color: '#a7f3d0', marginTop: 2 }}>
                    <strong>{speedChampion?.latency_ms} ms</strong> response time &bull; {speedChampion?.parameter_count} params
                  </div>
                </div>
              </div>

              {/* Accuracy Champion Card */}
              <div
                style={{
                  background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(49, 46, 129, 0.2) 100%)',
                  border: '1px solid rgba(99, 102, 241, 0.3)',
                  borderRadius: 12,
                  padding: '14px 18px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 14,
                }}
              >
                <div
                  style={{
                    width: 44,
                    height: 44,
                    borderRadius: 10,
                    background: 'rgba(99, 102, 241, 0.2)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: '#818cf8',
                    fontSize: 22,
                  }}
                >
                  <i className="bi bi-bullseye" />
                </div>
                <div>
                  <div style={{ fontSize: 11, fontWeight: 700, color: '#818cf8', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                    Accuracy & Retrieval Leader
                  </div>
                  <div style={{ fontSize: 15, fontWeight: 700, color: 'white', marginTop: 1 }}>
                    {accuracyChampion?.model_name.split('/').pop()}
                  </div>
                  <div style={{ fontSize: 12, color: '#c7d2fe', marginTop: 2 }}>
                    <strong>{accuracyChampion?.top_score_pct}%</strong> top match &bull; MTEB: {accuracyChampion?.mteb_score} NDCG
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Model Cards Grid */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
            {filteredModels.map((m) => {
              const isSpeedWinner = m.model_id === data?.speed_champion_id;
              const isAccuracyWinner = m.model_id === data?.accuracy_champion_id;

              return (
                <div
                  key={m.model_id}
                  style={{
                    background: 'rgba(30, 41, 59, 0.4)',
                    border: isAccuracyWinner
                      ? '1px solid rgba(99, 102, 241, 0.5)'
                      : isSpeedWinner
                      ? '1px solid rgba(16, 185, 129, 0.5)'
                      : '1px solid rgba(255, 255, 255, 0.08)',
                    borderRadius: 14,
                    padding: '20px',
                    position: 'relative',
                    boxShadow: '0 4px 20px rgba(0, 0, 0, 0.25)',
                    transition: 'border-color 0.2s ease',
                  }}
                >
                  {/* Model Header */}
                  <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap', marginBottom: 16 }}>
                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                        <h3 style={{ fontSize: 16, fontWeight: 700, margin: 0, color: 'white' }}>
                          {m.model_name}
                        </h3>
                        <span
                          style={{
                            fontSize: 11,
                            padding: '2px 8px',
                            borderRadius: 12,
                            background: 'rgba(255, 255, 255, 0.08)',
                            color: '#94a3b8',
                            fontWeight: 600,
                          }}
                        >
                          {m.family}
                        </span>
                        <span
                          style={{
                            fontSize: 11,
                            padding: '2px 8px',
                            borderRadius: 12,
                            background: isSpeedWinner ? 'rgba(16, 185, 129, 0.2)' : isAccuracyWinner ? 'rgba(99, 102, 241, 0.2)' : 'rgba(59, 130, 246, 0.15)',
                            color: isSpeedWinner ? '#34d399' : isAccuracyWinner ? '#818cf8' : '#60a5fa',
                            fontWeight: 600,
                          }}
                        >
                          {m.badge}
                        </span>
                      </div>
                      <div style={{ fontSize: 12.5, color: '#94a3b8', marginTop: 4 }}>
                        {m.description}
                      </div>
                    </div>

                    {/* Architecture Specs Pill Tags */}
                    <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                      <div style={{ background: 'rgba(15, 23, 42, 0.6)', padding: '4px 10px', borderRadius: 8, fontSize: 11, border: '1px solid rgba(255,255,255,0.06)' }}>
                        <span style={{ color: '#64748b' }}>Dim:</span> <strong>{m.dimension}d</strong>
                      </div>
                      <div style={{ background: 'rgba(15, 23, 42, 0.6)', padding: '4px 10px', borderRadius: 8, fontSize: 11, border: '1px solid rgba(255,255,255,0.06)' }}>
                        <span style={{ color: '#64748b' }}>Params:</span> <strong>{m.parameter_count}</strong>
                      </div>
                      <div style={{ background: 'rgba(15, 23, 42, 0.6)', padding: '4px 10px', borderRadius: 8, fontSize: 11, border: '1px solid rgba(255,255,255,0.06)' }}>
                        <span style={{ color: '#64748b' }}>Context:</span> <strong>{m.context_tokens} tokens</strong>
                      </div>
                      <div style={{ background: 'rgba(15, 23, 42, 0.6)', padding: '4px 10px', borderRadius: 8, fontSize: 11, border: '1px solid rgba(255,255,255,0.06)' }}>
                        <span style={{ color: '#64748b' }}>Memory:</span> <strong>{m.memory_footprint}</strong>
                      </div>
                    </div>
                  </div>

                  {/* Benchmark Performance Meters */}
                  <div
                    style={{
                      display: 'grid',
                      gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                      gap: 12,
                      padding: '12px 16px',
                      background: 'rgba(15, 23, 42, 0.5)',
                      borderRadius: 10,
                      marginBottom: 16,
                      border: '1px solid rgba(255, 255, 255, 0.05)',
                    }}
                  >
                    {/* Latency */}
                    <div>
                      <div style={{ fontSize: 11, color: '#94a3b8', display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                        <span>Search Latency</span>
                        <strong style={{ color: m.latency_ms < 20 ? '#34d399' : m.latency_ms < 35 ? '#fbbf24' : '#f87171' }}>
                          {m.latency_ms} ms
                        </strong>
                      </div>
                      <div style={{ height: 6, borderRadius: 3, background: 'rgba(255,255,255,0.1)', overflow: 'hidden' }}>
                        <div
                          style={{
                            height: '100%',
                            width: `${Math.min(100, (m.latency_ms / 60) * 100)}%`,
                            background: m.latency_ms < 20 ? '#10b981' : m.latency_ms < 35 ? '#f59e0b' : '#ef4444',
                            borderRadius: 3,
                          }}
                        />
                      </div>
                    </div>

                    {/* Top Match Accuracy */}
                    <div>
                      <div style={{ fontSize: 11, color: '#94a3b8', display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                        <span>Top Match Accuracy</span>
                        <strong style={{ color: '#60a5fa' }}>{m.top_score_pct}%</strong>
                      </div>
                      <div style={{ height: 6, borderRadius: 3, background: 'rgba(255,255,255,0.1)', overflow: 'hidden' }}>
                        <div
                          style={{
                            height: '100%',
                            width: `${m.top_score_pct}%`,
                            background: 'linear-gradient(90deg, #3b82f6, #6366f1)',
                            borderRadius: 3,
                          }}
                        />
                      </div>
                    </div>

                    {/* Academic MTEB Retrieval Score */}
                    <div>
                      <div style={{ fontSize: 11, color: '#94a3b8', display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                        <span>MTEB Retrieval (NDCG@10)</span>
                        <strong style={{ color: '#c084fc' }}>{m.mteb_score}</strong>
                      </div>
                      <div style={{ height: 6, borderRadius: 3, background: 'rgba(255,255,255,0.1)', overflow: 'hidden' }}>
                        <div
                          style={{
                            height: '100%',
                            width: `${(m.mteb_score / 70) * 100}%`,
                            background: 'linear-gradient(90deg, #8b5cf6, #c084fc)',
                            borderRadius: 3,
                          }}
                        />
                      </div>
                    </div>
                  </div>

                  {/* Deep Analysis Columns: Flaws & Strengths */}
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 14, marginBottom: 16 }}>
                    {/* Architectural Flaws & Limitations */}
                    <div
                      style={{
                        background: 'rgba(239, 68, 68, 0.06)',
                        border: '1px solid rgba(239, 68, 68, 0.2)',
                        borderRadius: 10,
                        padding: '12px 14px',
                      }}
                    >
                      <div style={{ fontSize: 12, fontWeight: 700, color: '#f87171', display: 'flex', alignItems: 'center', gap: 6, marginBottom: 8 }}>
                        <i className="bi bi-exclamation-octagon-fill" />
                        <span>Critical Flaws & Bottlenecks</span>
                      </div>
                      <ul style={{ margin: 0, paddingLeft: 18, fontSize: 12, color: '#fca5a5', lineHeight: 1.5 }}>
                        {m.flaws.map((flaw, i) => (
                          <li key={i} style={{ marginBottom: 4 }}>{flaw}</li>
                        ))}
                      </ul>
                    </div>

                    {/* Strengths & Best For */}
                    <div
                      style={{
                        background: 'rgba(16, 185, 129, 0.06)',
                        border: '1px solid rgba(16, 185, 129, 0.2)',
                        borderRadius: 10,
                        padding: '12px 14px',
                      }}
                    >
                      <div style={{ fontSize: 12, fontWeight: 700, color: '#34d399', display: 'flex', alignItems: 'center', gap: 6, marginBottom: 8 }}>
                        <i className="bi bi-shield-check" />
                        <span>Key Strengths & Optimal Use</span>
                      </div>
                      <ul style={{ margin: 0, paddingLeft: 18, fontSize: 12, color: '#a7f3d0', lineHeight: 1.5 }}>
                        {m.strengths.map((strength, i) => (
                          <li key={i} style={{ marginBottom: 4 }}>{strength}</li>
                        ))}
                      </ul>
                      <div style={{ marginTop: 8, fontSize: 11.5, color: '#6ee7b7', borderTop: '1px solid rgba(16, 185, 129, 0.15)', paddingTop: 6 }}>
                        <strong>Best For:</strong> {m.best_for}
                      </div>
                    </div>
                  </div>

                  {/* Top Matching Files for Current Query */}
                  {m.top_matches && m.top_matches.length > 0 && (
                    <div style={{ background: 'rgba(15, 23, 42, 0.4)', borderRadius: 8, padding: '10px 14px', border: '1px solid rgba(255, 255, 255, 0.04)' }}>
                      <div style={{ fontSize: 11.5, fontWeight: 600, color: '#94a3b8', marginBottom: 8, display: 'flex', alignItems: 'center', gap: 6 }}>
                        <i className="bi bi-file-earmark-check" style={{ color: '#60a5fa' }} />
                        <span>Top Retrieved Files for "{query}"</span>
                      </div>
                      <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
                        {m.top_matches.map((file) => (
                          <div
                            key={file.file_id}
                            style={{
                              background: 'rgba(30, 41, 59, 0.8)',
                              border: '1px solid rgba(255, 255, 255, 0.08)',
                              borderRadius: 6,
                              padding: '6px 10px',
                              display: 'flex',
                              alignItems: 'center',
                              gap: 8,
                              fontSize: 12,
                            }}
                          >
                            <span style={{ color: '#38bdf8', fontWeight: 600 }}>{file.name}</span>
                            <span
                              style={{
                                fontSize: 10,
                                background: 'rgba(59, 130, 246, 0.2)',
                                color: '#93c5fd',
                                padding: '1px 6px',
                                borderRadius: 10,
                                fontWeight: 700,
                              }}
                            >
                              {file.match_percentage}%
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* Footer */}
        <div
          style={{
            padding: '12px 24px',
            borderTop: '1px solid rgba(255, 255, 255, 0.08)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            background: 'rgba(15, 23, 42, 0.95)',
            fontSize: 12,
            color: '#64748b',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <i className="bi bi-cpu" />
            <span>Local Offline Inference Architecture &bull; Evaluated {data?.total_candidates_evaluated || 0} candidate files</span>
          </div>
          <button
            onClick={onClose}
            style={{
              background: 'rgba(255, 255, 255, 0.08)',
              border: '1px solid rgba(255, 255, 255, 0.15)',
              color: 'white',
              padding: '6px 16px',
              borderRadius: 6,
              fontSize: 12,
              fontWeight: 600,
              cursor: 'pointer',
            }}
          >
            Close Lab
          </button>
        </div>
      </div>
    </div>
  );
}
