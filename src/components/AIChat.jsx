import React, { useState, useRef, useEffect } from 'react';
import { search as apiSearch } from '../services/searchService';
import SearchResult from './SearchResult';
import LoadingSpinner from './LoadingSpinner';
import ModelComparisonModal from './ModelComparisonModal';

const suggestions = [
  'Find my fees in local drive',
  'Search for thejas in google drive',
  'Show invoices in onedrive',
  'Find resume in local drive under folder Downloads',
];

function Message({ role, content, results, loading, showRelevance, onToggleRelevance, onOpenComparison }) {
  const isUser = role === 'user';

  return (
    <div className={`chat-message-row ${isUser ? 'user' : ''}`}>
      <div className={`chat-avatar ${isUser ? 'user' : 'ai'}`}>
        {isUser ? <i className="bi bi-person" /> : <i className="bi bi-cpu" />}
      </div>
      <div className={`chat-bubble ${isUser ? 'user' : 'ai'}`}>
        <div className="chat-bubble-inner">
          {loading ? (
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <div className="spinner" style={{ width: 16, height: 16, borderWidth: 2 }} />
              <span style={{ fontSize: 13, color: 'var(--color-text-muted)' }}>AI is searching your files...</span>
            </div>
          ) : (
            <>
              <span style={{ color: isUser ? 'white' : 'var(--color-text-primary)', fontSize: 14 }}>{content}</span>
              {results && results.length > 0 && (
                <div style={{ marginTop: 14 }}>
                  {/* Results Subheader with Relevance Explanation Toggle Switch */}
                  <div
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      padding: '8px 12px',
                      marginBottom: 12,
                      background: 'rgba(255, 255, 255, 0.03)',
                      borderRadius: 8,
                      border: '1px solid var(--color-border-light)',
                      flexWrap: 'wrap',
                      gap: 8,
                    }}
                  >
                    <div style={{ fontSize: 12, color: 'var(--color-text-secondary)', display: 'flex', alignItems: 'center', gap: 6 }}>
                      <i className="bi bi-collection" style={{ color: 'var(--color-primary)' }} />
                      <span><strong>{results.length}</strong> matching file{results.length !== 1 ? 's' : ''} retrieved</span>
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                      {/* Compare 5 Models button */}
                      <button
                        type="button"
                        onClick={() => onOpenComparison && onOpenComparison()}
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: 6,
                          background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.15), rgba(139, 92, 246, 0.15))',
                          border: '1px solid rgba(99, 102, 241, 0.4)',
                          color: '#a5b4fc',
                          padding: '4px 10px',
                          borderRadius: 16,
                          cursor: 'pointer',
                          fontSize: 11.5,
                          fontWeight: 600,
                          transition: 'all 0.2s ease',
                        }}
                        title="Benchmark this search across 5 open-source embedding models"
                      >
                        <i className="bi bi-speedometer2" style={{ color: '#818cf8' }} />
                        <span>Compare 5 Models</span>
                      </button>

                      {/* Master Switch: Explain Relevance */}
                      <button
                        type="button"
                        onClick={onToggleRelevance}
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: 8,
                          background: showRelevance ? 'rgba(59, 130, 246, 0.15)' : 'rgba(255, 255, 255, 0.04)',
                          border: showRelevance ? '1px solid rgba(59, 130, 246, 0.5)' : '1px solid var(--color-border)',
                          color: showRelevance ? '#60a5fa' : 'var(--color-text-muted)',
                          padding: '4px 10px',
                          borderRadius: 16,
                          cursor: 'pointer',
                          fontSize: 11.5,
                          fontWeight: 600,
                          transition: 'all 0.2s ease',
                        }}
                        title="Toggle detailed relevance insights explaining why each file matched"
                      >
                        <i className="bi bi-stars" style={{ color: showRelevance ? '#60a5fa' : 'inherit' }} />
                        <span>Explain Relevance</span>
                        <div
                          style={{
                            width: 28,
                            height: 16,
                            borderRadius: 8,
                            background: showRelevance ? '#3b82f6' : 'rgba(255, 255, 255, 0.2)',
                            position: 'relative',
                            transition: 'background 0.2s',
                          }}
                        >
                          <div
                            style={{
                              width: 12,
                              height: 12,
                              borderRadius: '50%',
                              background: 'white',
                              position: 'absolute',
                              top: 2,
                              left: showRelevance ? 14 : 2,
                              transition: 'left 0.2s',
                            }}
                          />
                        </div>
                      </button>
                    </div>
                  </div>

                  {/* Results Grid */}
                  <div className="chat-results-grid">
                    {results.map((file) => (
                      <SearchResult key={file.id} file={file} showRelevance={showRelevance} />
                    ))}
                  </div>
                </div>
              )}
            </>
          )}
        </div>
        <div className="chat-meta" style={{ textAlign: isUser ? 'right' : 'left' }}>
          {new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </div>
      </div>
    </div>
  );
}

export default function AIChat({ initialQuery = '' }) {
  const [messages, setMessages] = useState([
    {
      id: 0,
      role: 'ai',
      content: 'Hello! I can help you find files across all your connected storage providers. What are you looking for?',
      results: [],
    },
  ]);
  const [input, setInput] = useState(initialQuery);
  const [loading, setLoading] = useState(false);
  const [firstSent, setFirstSent] = useState(false);
  const [showRelevance, setShowRelevance] = useState(() => {
    return localStorage.getItem('ai_fm_explain_relevance') === 'true';
  });
  const [isComparisonOpen, setIsComparisonOpen] = useState(false);
  const [comparisonQuery, setComparisonQuery] = useState('');
  const bottomRef = useRef(null);

  const toggleRelevance = () => {
    setShowRelevance((prev) => {
      const next = !prev;
      localStorage.setItem('ai_fm_explain_relevance', String(next));
      return next;
    });
  };

  const openComparison = (queryOverride) => {
    const lastUserMsg = [...messages].reverse().find((m) => m.role === 'user');
    const target = queryOverride || lastUserMsg?.content || input || initialQuery || 'find my final year fees';
    setComparisonQuery(target);
    setIsComparisonOpen(true);
  };

  useEffect(() => {
    if (initialQuery && !firstSent) {
      setFirstSent(true);
      handleSend(initialQuery);
    }
  }, [initialQuery]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, showRelevance]);

  const handleSend = async (query) => {
    const q = (query || input).trim();
    if (!q || loading) return;

    const userMsgId = 'user_' + Date.now() + '_' + Math.random().toString(36).slice(2, 7);
    const loadingId = 'ai_' + Date.now() + '_' + Math.random().toString(36).slice(2, 7);
    setInput('');
    setMessages((prev) => [
      ...prev,
      { id: userMsgId, role: 'user', content: q },
      { id: loadingId, role: 'ai', content: '', loading: true }
    ]);
    setLoading(true);

    try {
      const { files, message } = await apiSearch(q);
      setMessages((prev) =>
        prev.map((m) =>
          m.id === loadingId
            ? { ...m, loading: false, content: message, results: files }
            : m
        )
      );
    } catch {
      setMessages((prev) =>
        prev.map((m) =>
          m.id === loadingId
            ? { ...m, loading: false, content: 'Something went wrong. Please try again.' }
            : m
        )
      );
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', minHeight: 500 }}>
      {/* Header Bar with Global Explain Relevance & Compare 5 Models buttons */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          paddingBottom: 12,
          borderBottom: '1px solid var(--color-border-light)',
          marginBottom: 8,
          flexWrap: 'wrap',
          gap: 10,
        }}
      >
        <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--color-text-secondary)', display: 'flex', alignItems: 'center', gap: 6 }}>
          <i className="bi bi-chat-left-dots" style={{ color: 'var(--color-primary)' }} />
          <span>Interactive AI Search Session</span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
          {/* Top Bar Compare 5 Models Trigger */}
          <button
            type="button"
            onClick={() => openComparison()}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 6,
              background: 'linear-gradient(135deg, rgba(59, 130, 246, 0.2), rgba(139, 92, 246, 0.2))',
              border: '1px solid rgba(99, 102, 241, 0.5)',
              color: '#c7d2fe',
              padding: '5px 12px',
              borderRadius: 16,
              cursor: 'pointer',
              fontSize: 12,
              fontWeight: 600,
              transition: 'all 0.2s ease',
              boxShadow: '0 0 12px rgba(99, 102, 241, 0.2)',
            }}
            title="Benchmark current query across 5 open-source embedding models"
          >
            <i className="bi bi-speedometer2" style={{ color: '#a5b4fc' }} />
            <span>Compare 5 Models</span>
          </button>

          {/* Separate Window Pop-out */}
          <button
            type="button"
            onClick={() => {
              const lastUserMsg = messages.filter(m => m.role === 'user').slice(-1)[0]?.content;
              const q = input.trim() || lastUserMsg || comparisonQuery || 'find my final year fees';
              window.open(`/models?q=${encodeURIComponent(q)}`, '_blank', 'width=1320,height=920,menubar=no,toolbar=no,location=no,status=no');
            }}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 6,
              background: 'rgba(255, 255, 255, 0.05)',
              border: '1px solid rgba(255, 255, 255, 0.15)',
              color: '#93c5fd',
              padding: '5px 10px',
              borderRadius: 16,
              cursor: 'pointer',
              fontSize: 12,
              fontWeight: 500,
              transition: 'all 0.2s ease',
            }}
            title="Open detailed model breakdown in a separate window"
          >
            <i className="bi bi-box-arrow-up-right" style={{ fontSize: 11 }} />
            <span>Separate Window</span>
          </button>

          {/* Master Switch: Explain Relevance */}
          <button
            type="button"
            onClick={toggleRelevance}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              background: showRelevance ? 'rgba(59, 130, 246, 0.15)' : 'rgba(255, 255, 255, 0.04)',
              border: showRelevance ? '1px solid rgba(59, 130, 246, 0.5)' : '1px solid var(--color-border)',
              color: showRelevance ? '#60a5fa' : 'var(--color-text-muted)',
              padding: '5px 12px',
              borderRadius: 16,
              cursor: 'pointer',
              fontSize: 12,
              fontWeight: 600,
              transition: 'all 0.2s ease',
            }}
            title="Toggle relevance explanations for all search results"
          >
            <i className="bi bi-stars" style={{ color: showRelevance ? '#60a5fa' : 'inherit' }} />
            <span>Explain Relevance: {showRelevance ? 'ON' : 'OFF'}</span>
            <div
              style={{
                width: 32,
                height: 18,
                borderRadius: 9,
                background: showRelevance ? '#3b82f6' : 'rgba(255, 255, 255, 0.2)',
                position: 'relative',
                transition: 'background 0.2s',
              }}
            >
              <div
                style={{
                  width: 14,
                  height: 14,
                  borderRadius: '50%',
                  background: 'white',
                  position: 'absolute',
                  top: 2,
                  left: showRelevance ? 16 : 2,
                  transition: 'left 0.2s',
                }}
              />
            </div>
          </button>
        </div>
      </div>

      {/* Messages */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '8px 0' }}>
        <div className="ai-chat-container">
          {messages.map((m) => (
            <Message
              key={m.id}
              role={m.role}
              content={m.content}
              results={m.results}
              loading={m.loading}
              showRelevance={showRelevance}
              onToggleRelevance={toggleRelevance}
              onOpenComparison={() => openComparison()}
            />
          ))}
          <div ref={bottomRef} />
        </div>

        {/* Suggestion chips (only at start) */}
        {messages.length === 1 && (
          <div style={{ padding: '8px 0 16px' }}>
            <div style={{ fontSize: 12, color: 'var(--color-text-muted)', marginBottom: 10 }}>
              Try asking:
            </div>
            <div className="ai-suggestions">
              {suggestions.map((s) => (
                <button
                  key={s}
                  className="ai-suggestion-chip"
                  onClick={() => handleSend(s)}
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Input */}
      <div
        style={{
          borderTop: '1px solid var(--color-border)',
          paddingTop: 14,
          display: 'flex',
          gap: 10,
          alignItems: 'flex-end',
        }}
      >
        <div className="input-group-custom" style={{ flex: 1 }}>
          <i className="bi bi-stars input-icon" style={{ color: 'var(--color-primary)' }} />
          <input
            type="text"
            className="form-control-custom"
            placeholder="Ask AI to find your files (e.g., 'find my final year fees')..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={loading}
          />
        </div>
        <button
          className="btn-primary-custom"
          onClick={() => handleSend()}
          disabled={loading || !input.trim()}
          style={{ padding: '11px 18px', borderRadius: 'var(--radius-md)' }}
        >
          {loading ? (
            <div className="spinner" style={{ width: 16, height: 16, borderWidth: 2, borderColor: 'rgba(255,255,255,0.3)', borderTopColor: 'white' }} />
          ) : (
            <i className="bi bi-send" />
          )}
        </button>
      </div>

      {/* 5 Open-Source Models Comparison Modal */}
      <ModelComparisonModal
        isOpen={isComparisonOpen}
        onClose={() => setIsComparisonOpen(false)}
        initialQuery={comparisonQuery}
      />
    </div>
  );
}

