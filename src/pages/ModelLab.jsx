import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { compareSearchModels } from '../services/searchService';
import toast from 'react-hot-toast';

export default function ModelLab() {
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();
  const initialQ = searchParams.get('q') || 'project report';

  const [query, setQuery] = useState(initialQ);
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [selectedFilter, setSelectedFilter] = useState('all'); // 'all', 'speed', 'accuracy'
  const [activeModelTab, setActiveModelTab] = useState(null);

  useEffect(() => {
    runBenchmark(initialQ);
  }, []);

  const runBenchmark = async (benchmarkQuery) => {
    const q = (benchmarkQuery || query).trim();
    if (!q) return;
    setLoading(true);
    setError(null);
    try {
      setSearchParams({ q });
      const res = await compareSearchModels(q, { limitPerModel: 4 });
      setData(res);
      if (res?.models?.length && !activeModelTab) {
        setActiveModelTab(res.models[0].model_id);
      }
    } catch (err) {
      console.error('Benchmark error:', err);
      setError('Failed to benchmark models. Please ensure the backend is running.');
      toast.error('Failed to run model benchmark');
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

  const models = data?.models || [];
  const speedChampion = models.find((m) => m.model_id === data?.speed_champion_id) || models[0];
  const accuracyChampion = models.find((m) => m.model_id === data?.accuracy_champion_id) || models[1];

  const filteredModels = models.filter((m) => {
    if (selectedFilter === 'speed') return m.model_id === data?.speed_champion_id;
    if (selectedFilter === 'accuracy') return m.model_id === data?.accuracy_champion_id;
    return true;
  });

  const selectedModelData = models.find((m) => m.model_id === activeModelTab) || models[0];

  return (
    <div style={{ color: '#f8fafc', paddingBottom: 60 }}>
      {/* Top Banner Header */}
      <div
        style={{
          background: 'linear-gradient(135deg, rgba(15, 23, 42, 0.95) 0%, rgba(30, 41, 59, 0.95) 100%)',
          borderRadius: 16,
          border: '1px solid rgba(255, 255, 255, 0.12)',
          padding: '24px 28px',
          marginBottom: 24,
          boxShadow: '0 20px 40px -15px rgba(0, 0, 0, 0.6), 0 0 30px rgba(59, 130, 246, 0.1)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 16 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
            <div
              style={{
                width: 48,
                height: 48,
                borderRadius: 12,
                background: 'linear-gradient(135deg, #3b82f6, #8b5cf6)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                boxShadow: '0 0 20px rgba(99, 102, 241, 0.5)',
              }}
            >
              <i className="bi bi-speedometer2" style={{ fontSize: 24, color: 'white' }} />
            </div>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <h1 style={{ fontSize: 22, fontWeight: 700, margin: 0, letterSpacing: '-0.02em', color: 'white' }}>
                  AI Model Comparison & Architecture Lab
                </h1>
                <span
                  style={{
                    fontSize: 11,
                    padding: '3px 10px',
                    borderRadius: 20,
                    background: 'rgba(59, 130, 246, 0.2)',
                    color: '#60a5fa',
                    border: '1px solid rgba(59, 130, 246, 0.4)',
                    fontWeight: 600,
                  }}
                >
                  5 Active Search Models
                </span>
              </div>
              <p style={{ margin: '4px 0 0', fontSize: 13, color: '#94a3b8' }}>
                Multi-model side-by-side inference profiling: latency (ms), precision rankings, memory specs, strengths, and flaws.
              </p>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <button
              onClick={() => window.open(window.location.href, '_blank', 'width=1280,height=900')}
              className="btn-outline-custom"
              style={{ padding: '8px 14px', fontSize: 12.5, gap: 6, display: 'flex', alignItems: 'center' }}
              title="Pop out in a separate standalone window"
            >
              <i className="bi bi-box-arrow-up-right" />
              Pop Out Window
            </button>
            <button
              onClick={() => navigate('/ai-search')}
              className="btn-outline-custom"
              style={{ padding: '8px 14px', fontSize: 12.5, gap: 6, display: 'flex', alignItems: 'center' }}
            >
              <i className="bi bi-chat-dots" />
              Back to AI Search
            </button>
          </div>
        </div>

        {/* Benchmark Query Bar */}
        <div style={{ marginTop: 20, display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              flex: 1,
              minWidth: 320,
              background: 'rgba(15, 23, 42, 0.8)',
              border: '1px solid rgba(255, 255, 255, 0.15)',
              borderRadius: 10,
              padding: '8px 14px',
              gap: 10,
            }}
          >
            <i className="bi bi-search" style={{ color: '#60a5fa', fontSize: 15 }} />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Enter benchmark query (e.g. 'find my project report', 'thejas fees', 'appointment letter')..."
              style={{
                background: 'transparent',
                border: 'none',
                outline: 'none',
                color: 'white',
                fontSize: 14,
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
              padding: '10px 22px',
              borderRadius: 10,
              fontSize: 13.5,
              fontWeight: 600,
              cursor: loading ? 'not-allowed' : 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              boxShadow: '0 4px 12px rgba(37, 99, 235, 0.35)',
            }}
          >
            {loading ? (
              <>
                <div className="spinner" style={{ width: 16, height: 16, borderWidth: 2 }} />
                <span>Benchmarking 5 Models...</span>
              </>
            ) : (
              <>
                <i className="bi bi-lightning-charge-fill" />
                <span>Run 5-Model Benchmark</span>
              </>
            )}
          </button>
        </div>

        {/* Quick Sample Queries */}
        <div style={{ marginTop: 12, display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
          <span style={{ fontSize: 12, color: '#64748b', fontWeight: 600 }}>Quick Benchmarks:</span>
          {[
            'thejas fees',
            'project report',
            'appointment letter',
            'invoices from june',
            'resume computer science',
          ].map((sample) => (
            <button
              key={sample}
              onClick={() => {
                setQuery(sample);
                runBenchmark(sample);
              }}
              style={{
                background: 'rgba(255, 255, 255, 0.05)',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                color: '#cbd5e1',
                padding: '3px 10px',
                borderRadius: 14,
                fontSize: 11.5,
                cursor: 'pointer',
                transition: 'all 0.15s ease',
              }}
            >
              {sample}
            </button>
          ))}
        </div>
      </div>

      {error && (
        <div
          style={{
            padding: 14,
            borderRadius: 10,
            background: 'rgba(239, 68, 68, 0.15)',
            border: '1px solid rgba(239, 68, 68, 0.3)',
            color: '#fca5a5',
            fontSize: 13,
            marginBottom: 20,
            display: 'flex',
            alignItems: 'center',
            gap: 10,
          }}
        >
          <i className="bi bi-exclamation-triangle-fill" style={{ fontSize: 16 }} />
          <span>{error}</span>
        </div>
      )}

      {/* Top Champions Row */}
      {data && (
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
            gap: 16,
            marginBottom: 24,
          }}
        >
          {/* Speed Champion */}
          <div
            style={{
              background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.12) 0%, rgba(6, 78, 59, 0.25) 100%)',
              border: '1px solid rgba(16, 185, 129, 0.35)',
              borderRadius: 14,
              padding: '16px 20px',
              display: 'flex',
              alignItems: 'center',
              gap: 16,
            }}
          >
            <div
              style={{
                width: 48,
                height: 48,
                borderRadius: 12,
                background: 'rgba(16, 185, 129, 0.2)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#34d399',
                fontSize: 24,
              }}
            >
              <i className="bi bi-lightning-charge-fill" />
            </div>
            <div>
              <div style={{ fontSize: 11, fontWeight: 700, color: '#34d399', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                ⚡ Speed Champion
              </div>
              <div style={{ fontSize: 16, fontWeight: 700, color: 'white', marginTop: 2 }}>
                {speedChampion?.model_name}
              </div>
              <div style={{ fontSize: 12.5, color: '#a7f3d0', marginTop: 3 }}>
                <strong>{speedChampion?.latency_ms} ms</strong> response time &bull; {speedChampion?.parameter_count} params &bull; Context: {speedChampion?.context_tokens} tokens
              </div>
            </div>
          </div>

          {/* Accuracy Champion */}
          <div
            style={{
              background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.12) 0%, rgba(49, 46, 129, 0.25) 100%)',
              border: '1px solid rgba(99, 102, 241, 0.35)',
              borderRadius: 14,
              padding: '16px 20px',
              display: 'flex',
              alignItems: 'center',
              gap: 16,
            }}
          >
            <div
              style={{
                width: 48,
                height: 48,
                borderRadius: 12,
                background: 'rgba(99, 102, 241, 0.2)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#818cf8',
                fontSize: 24,
              }}
            >
              <i className="bi bi-bullseye" />
            </div>
            <div>
              <div style={{ fontSize: 11, fontWeight: 700, color: '#818cf8', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                🎯 Top Match Precision
              </div>
              <div style={{ fontSize: 16, fontWeight: 700, color: 'white', marginTop: 2 }}>
                {accuracyChampion?.model_name}
              </div>
              <div style={{ fontSize: 12.5, color: '#c7d2fe', marginTop: 3 }}>
                <strong>{accuracyChampion?.top_score_pct}%</strong> top match score &bull; {accuracyChampion?.architecture?.slice(0, 45)}...
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Model Cards Grid */}
      <div style={{ marginBottom: 16, display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 10 }}>
        <h2 style={{ fontSize: 17, fontWeight: 700, margin: 0, color: '#f1f5f9' }}>
          Side-by-Side Model Architectures & Performance
        </h2>

        {/* Filter Pills */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          {[
            { id: 'all', label: 'All 5 Models' },
            { id: 'speed', label: '⚡ Speed Winner' },
            { id: 'accuracy', label: '🎯 Accuracy Leader' },
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
              }}
            >
              {f.label}
            </button>
          ))}
        </div>
      </div>

      {/* 5 Models Comparative Cards */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))',
          gap: 16,
          marginBottom: 30,
        }}
      >
        {filteredModels.map((m) => {
          const isSelected = activeModelTab === m.model_id;
          return (
            <div
              key={m.model_id}
              onClick={() => setActiveModelTab(m.model_id)}
              style={{
                background: isSelected ? 'rgba(30, 41, 59, 0.95)' : 'rgba(15, 23, 42, 0.7)',
                border: isSelected ? '2px solid #3b82f6' : '1px solid rgba(255, 255, 255, 0.08)',
                borderRadius: 14,
                padding: '18px 20px',
                cursor: 'pointer',
                transition: 'all 0.2s ease',
                boxShadow: isSelected ? '0 0 25px rgba(59, 130, 246, 0.2)' : 'none',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 }}>
                <span
                  style={{
                    fontSize: 11,
                    fontWeight: 700,
                    padding: '2px 8px',
                    borderRadius: 10,
                    background: m.badge.includes('Speed') ? 'rgba(16, 185, 129, 0.2)' : 'rgba(99, 102, 241, 0.2)',
                    color: m.badge.includes('Speed') ? '#34d399' : '#a5b4fc',
                    border: '1px solid rgba(255, 255, 255, 0.1)',
                  }}
                >
                  {m.badge}
                </span>
                <span style={{ fontSize: 11, color: '#64748b' }}>{m.dimension}-dim vector</span>
              </div>

              <div style={{ fontSize: 15, fontWeight: 700, color: 'white', marginBottom: 4 }}>
                {m.model_name}
              </div>
              <div style={{ fontSize: 12, color: '#94a3b8', marginBottom: 14 }}>
                {m.family}
              </div>

              {/* Metrics Row */}
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: '1fr 1fr 1fr',
                  background: 'rgba(0, 0, 0, 0.25)',
                  borderRadius: 8,
                  padding: '8px 10px',
                  marginBottom: 14,
                  textAlign: 'center',
                }}
              >
                <div>
                  <div style={{ fontSize: 10, color: '#64748b', textTransform: 'uppercase' }}>Latency</div>
                  <div style={{ fontSize: 14, fontWeight: 700, color: m.latency_ms < 50 ? '#34d399' : '#fbbf24' }}>
                    {m.latency_ms} ms
                  </div>
                </div>
                <div>
                  <div style={{ fontSize: 10, color: '#64748b', textTransform: 'uppercase' }}>Top Match</div>
                  <div style={{ fontSize: 14, fontWeight: 700, color: '#60a5fa' }}>
                    {m.top_score_pct}%
                  </div>
                </div>
                <div>
                  <div style={{ fontSize: 10, color: '#64748b', textTransform: 'uppercase' }}>Context</div>
                  <div style={{ fontSize: 14, fontWeight: 700, color: '#cbd5e1' }}>
                    {m.context_tokens} tok
                  </div>
                </div>
              </div>

              {/* Architecture & Specs */}
              <div style={{ fontSize: 12, color: '#cbd5e1', lineHeight: 1.5, marginBottom: 12 }}>
                {m.description}
              </div>

              {/* Top Strengths */}
              <div style={{ marginBottom: 10 }}>
                <div style={{ fontSize: 11, fontWeight: 700, color: '#34d399', marginBottom: 4, textTransform: 'uppercase' }}>
                  Key Strengths:
                </div>
                {m.strengths?.slice(0, 2).map((s, idx) => (
                  <div key={idx} style={{ fontSize: 11.5, color: '#a7f3d0', display: 'flex', alignItems: 'flex-start', gap: 6, marginBottom: 2 }}>
                    <i className="bi bi-check2-circle" style={{ color: '#34d399', flexShrink: 0, marginTop: 1 }} />
                    <span>{s}</span>
                  </div>
                ))}
              </div>

              {/* Critical Flaws & Trade-offs */}
              <div style={{ marginBottom: 14 }}>
                <div style={{ fontSize: 11, fontWeight: 700, color: '#f87171', marginBottom: 4, textTransform: 'uppercase' }}>
                  Critical Flaws & Limits:
                </div>
                {m.flaws?.slice(0, 2).map((flaw, idx) => (
                  <div key={idx} style={{ fontSize: 11.5, color: '#fca5a5', display: 'flex', alignItems: 'flex-start', gap: 6, marginBottom: 2 }}>
                    <i className="bi bi-x-circle" style={{ color: '#f87171', flexShrink: 0, marginTop: 1 }} />
                    <span>{flaw}</span>
                  </div>
                ))}
              </div>

              {/* Top Matches Preview */}
              <div>
                <div style={{ fontSize: 11, fontWeight: 700, color: '#94a3b8', marginBottom: 6, textTransform: 'uppercase' }}>
                  Top Ranked Files:
                </div>
                {m.top_matches && m.top_matches.length > 0 ? (
                  m.top_matches.slice(0, 3).map((match, idx) => (
                    <div
                      key={match.file_id || idx}
                      style={{
                        padding: '6px 8px',
                        background: 'rgba(255, 255, 255, 0.03)',
                        borderRadius: 6,
                        marginBottom: 4,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        fontSize: 11.5,
                      }}
                    >
                      <span style={{ color: '#f8fafc', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: 220 }}>
                        📄 {match.name}
                      </span>
                      <span style={{ color: '#60a5fa', fontWeight: 600 }}>{match.match_percentage}%</span>
                    </div>
                  ))
                ) : (
                  <div style={{ fontSize: 11, color: '#64748b', fontStyle: 'italic' }}>
                    No files evaluated yet. Run query above.
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Detailed Architecture Breakdown Window for Selected Model */}
      {selectedModelData && (
        <div
          style={{
            background: 'rgba(15, 23, 42, 0.85)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            borderRadius: 16,
            padding: '24px 28px',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
            <h3 style={{ fontSize: 18, fontWeight: 700, margin: 0, color: 'white', display: 'flex', alignItems: 'center', gap: 10 }}>
              <i className="bi bi-cpu" style={{ color: '#60a5fa' }} />
              Detailed Technical Specification: {selectedModelData.model_name}
            </h3>
            <span style={{ fontSize: 12, color: '#94a3b8' }}>
              Family: {selectedModelData.family}
            </span>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 12, marginBottom: 20 }}>
            <div style={{ background: 'rgba(255, 255, 255, 0.03)', padding: 12, borderRadius: 8 }}>
              <div style={{ fontSize: 11, color: '#64748b' }}>Parameter Count</div>
              <div style={{ fontSize: 16, fontWeight: 700, color: 'white', marginTop: 2 }}>{selectedModelData.parameter_count}</div>
            </div>
            <div style={{ background: 'rgba(255, 255, 255, 0.03)', padding: 12, borderRadius: 8 }}>
              <div style={{ fontSize: 11, color: '#64748b' }}>Vector Dimension</div>
              <div style={{ fontSize: 16, fontWeight: 700, color: 'white', marginTop: 2 }}>{selectedModelData.dimension} dims</div>
            </div>
            <div style={{ background: 'rgba(255, 255, 255, 0.03)', padding: 12, borderRadius: 8 }}>
              <div style={{ fontSize: 11, color: '#64748b' }}>Max Context Window</div>
              <div style={{ fontSize: 16, fontWeight: 700, color: 'white', marginTop: 2 }}>{selectedModelData.context_tokens} tokens</div>
            </div>
            <div style={{ background: 'rgba(255, 255, 255, 0.03)', padding: 12, borderRadius: 8 }}>
              <div style={{ fontSize: 11, color: '#64748b' }}>RAM Footprint</div>
              <div style={{ fontSize: 16, fontWeight: 700, color: 'white', marginTop: 2 }}>{selectedModelData.memory_footprint}</div>
            </div>
            <div style={{ background: 'rgba(255, 255, 255, 0.03)', padding: 12, borderRadius: 8 }}>
              <div style={{ fontSize: 11, color: '#64748b' }}>MTEB Retrieval Score</div>
              <div style={{ fontSize: 16, fontWeight: 700, color: '#60a5fa', marginTop: 2 }}>{selectedModelData.mteb_score}</div>
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
            <div>
              <div style={{ fontSize: 13, fontWeight: 700, color: '#34d399', marginBottom: 8, display: 'flex', alignItems: 'center', gap: 6 }}>
                <i className="bi bi-shield-check" />
                Comprehensive Strengths
              </div>
              <ul style={{ margin: 0, paddingLeft: 18, fontSize: 12.5, color: '#cbd5e1', lineHeight: 1.6 }}>
                {selectedModelData.strengths?.map((s, idx) => (
                  <li key={idx}>{s}</li>
                ))}
              </ul>
            </div>

            <div>
              <div style={{ fontSize: 13, fontWeight: 700, color: '#f87171', marginBottom: 8, display: 'flex', alignItems: 'center', gap: 6 }}>
                <i className="bi bi-exclamation-octagon" />
                Architectural Limitations & Flaws
              </div>
              <ul style={{ margin: 0, paddingLeft: 18, fontSize: 12.5, color: '#cbd5e1', lineHeight: 1.6 }}>
                {selectedModelData.flaws?.map((f, idx) => (
                  <li key={idx}>{f}</li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
