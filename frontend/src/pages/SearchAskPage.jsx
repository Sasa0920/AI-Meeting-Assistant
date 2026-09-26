import { useState, useEffect } from 'react';

export default function SearchAskPage({ onSelectMeeting }) {
  const [query, setQuery] = useState('');
  const [selectedMeetingId, setSelectedMeetingId] = useState('');
  const [meetings, setMeetings] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchMode, setSearchMode] = useState('rag'); // 'rag' | 'semantic'
  const [ragResult, setRagResult] = useState(null);
  const [semanticResults, setSemanticResults] = useState([]);
  const [error, setError] = useState(null);
  const [copiedAnswer, setCopiedAnswer] = useState(false);

  // Load indexed meetings for the dropdown filter
  useEffect(() => {
    fetch('http://localhost:8000/meetings')
      .then((res) => (res.ok ? res.json() : []))
      .then((data) => {
        setMeetings(data);
      })
      .catch((err) => console.error('Failed to load meetings for search filter:', err));
  }, []);

  const exampleQuestions = [
    'Who is fixing the token refresh bug and when is the PR due?',
    'What was decided regarding Redis caching migration?',
    'What caused the 45-minute outage on the reporting service?',
    'What did the team decide about PgBouncer max connections?',
    'When are the mobile app store marketing assets due?',
    'What is the annual compensation budget for the marketing team?',
  ];

  const handleSearch = async (queryText = query) => {
    const textToSearch = (queryText || '').trim();
    if (!textToSearch) return;

    setLoading(true);
    setError(null);
    setRagResult(null);
    setSemanticResults([]);

    try {
      if (searchMode === 'rag') {
        const payload = {
          query: textToSearch,
          meeting_id: selectedMeetingId || null,
          top_k: 5,
        };
        const res = await fetch('http://localhost:8000/rag/query', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });

        if (!res.ok) {
          const errData = await res.json().catch(() => ({}));
          throw new Error(errData.detail || 'Failed to query the knowledge base');
        }

        const data = await res.json();
        setRagResult(data);
      } else {
        const payload = {
          query: textToSearch,
          meeting_id: selectedMeetingId || null,
          limit: 6,
        };
        const res = await fetch('http://localhost:8000/rag/search', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });

        if (!res.ok) {
          const errData = await res.json().catch(() => ({}));
          throw new Error(errData.detail || 'Failed to perform semantic search');
        }

        const data = await res.json();
        setSemanticResults(data.results || []);
      }
    } catch (err) {
      console.error('Search error:', err);
      setError(err.message || 'Search request failed');
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSearch();
    }
  };

  const handleCopyAnswer = () => {
    if (!ragResult?.answer) return;
    navigator.clipboard.writeText(ragResult.answer);
    setCopiedAnswer(true);
    setTimeout(() => setCopiedAnswer(false), 2000);
  };

  const formatTimestamp = (start, end) => {
    if (start === null || start === undefined) return null;
    const formatSec = (sec) => {
      const m = Math.floor(sec / 60);
      const s = Math.floor(sec % 60);
      return `${m}:${s < 10 ? '0' : ''}${s}`;
    };
    return `${formatSec(start)} – ${formatSec(end)}`;
  };

  return (
    <div className="search-ask-container">
      {/* Hero Header */}
      <div className="search-hero">
        <div className="search-hero-badge">✦ Knowledge Base RAG</div>
        <h2 className="search-hero-title">Ask Questions Across All Meetings</h2>
        <p className="search-hero-subtitle">
          Query your team's historical discussions, decisions, and action items. Every answer is grounded strictly in indexed meeting recordings.
        </p>
      </div>

      {/* Main Search Input Area */}
      <div className="card search-card">
        <div className="search-modes-tabs">
          <button
            className={`search-mode-tab ${searchMode === 'rag' ? 'active' : ''}`}
            onClick={() => setSearchMode('rag')}
          >
            <span className="mode-icon">✦</span> AI Grounded Answer
          </button>
          <button
            className={`search-mode-tab ${searchMode === 'semantic' ? 'active' : ''}`}
            onClick={() => setSearchMode('semantic')}
          >
            <span className="mode-icon">🔍</span> Direct Vector Search
          </button>
        </div>

        <div className="search-input-wrapper">
          <svg className="search-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="11" cy="11" r="8"></circle>
            <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
          </svg>
          <input
            type="text"
            className="search-input"
            placeholder={
              searchMode === 'rag'
                ? "Ask a question (e.g. 'What was decided about the auth PR?')"
                : "Type search terms for semantic matching across transcripts..."
            }
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
          />
          {query && (
            <button className="clear-query-btn" onClick={() => setQuery('')} title="Clear text">
              ✕
            </button>
          )}
          <button
            className="button-primary search-submit-btn"
            onClick={() => handleSearch()}
            disabled={loading || !query.trim()}
          >
            {loading ? 'Searching...' : searchMode === 'rag' ? 'Ask AI' : 'Search'}
          </button>
        </div>

        {/* Filter Toolbar */}
        <div className="search-toolbar">
          <div className="filter-group">
            <label htmlFor="meeting-filter" className="filter-label">Filter Meeting:</label>
            <select
              id="meeting-filter"
              className="meeting-select"
              value={selectedMeetingId}
              onChange={(e) => setSelectedMeetingId(e.target.value)}
            >
              <option value="">All Indexed Meetings</option>
              {meetings.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.filename} {m.has_index ? '(Indexed)' : ''}
                </option>
              ))}
            </select>
          </div>

          <div className="example-chips-wrapper">
            <span className="example-label">Examples:</span>
            <div className="example-chips">
              {exampleQuestions.slice(0, 3).map((eq, i) => (
                <button
                  key={i}
                  className="example-chip"
                  onClick={() => {
                    setQuery(eq);
                    handleSearch(eq);
                  }}
                >
                  "{eq}"
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="alert-error" style={{ marginTop: '1.5rem' }}>
          <strong>Search Error:</strong> {error}
        </div>
      )}

      {/* Loading Indicator */}
      {loading && (
        <div className="card loading-card" style={{ marginTop: '1.5rem', textAlign: 'center', padding: '3.5rem 1.5rem' }}>
          <div className="loading-spinner"></div>
          <p style={{ marginTop: '1.25rem', color: 'var(--text-secondary)', fontWeight: 500 }}>
            {searchMode === 'rag'
              ? 'Retrieving relevant excerpts & synthesizing grounded answer...'
              : 'Searching vector knowledge base across indexed meetings...'}
          </p>
        </div>
      )}

      {/* RAG Answer Display */}
      {ragResult && !loading && (
        <div className="rag-result-section" style={{ marginTop: '2rem' }}>
          <div className={`card answer-card ${ragResult.insufficient_evidence ? 'warning' : 'success'}`}>
            <div className="answer-header">
              <div className="answer-badge">
                {ragResult.insufficient_evidence ? (
                  <span className="badge-insufficient">⚠️ Insufficient Evidence</span>
                ) : (
                  <span className="badge-grounded">✓ Grounded AI Answer</span>
                )}
              </div>
              {!ragResult.insufficient_evidence && (
                <button
                  className="copy-btn-inline"
                  onClick={handleCopyAnswer}
                  title="Copy answer to clipboard"
                >
                  {copiedAnswer ? '✓ Copied' : 'Copy Answer'}
                </button>
              )}
            </div>

            <div className="answer-text">
              <p>{ragResult.answer}</p>
            </div>

            {ragResult.insufficient_evidence && (
              <div className="insufficient-note">
                <p>
                  <strong>Note:</strong> To prevent hallucinations, the assistant only answers questions directly supported by indexed transcripts and intelligence records.
                </p>
              </div>
            )}
          </div>

          {/* Sources Section */}
          {ragResult.sources && ragResult.sources.length > 0 && (
            <div className="sources-section" style={{ marginTop: '2rem' }}>
              <div className="sources-header">
                <h3 className="section-title">Cited Sources & Context Excerpts ({ragResult.sources.length})</h3>
                <span className="sources-subtitle">Direct excerpts retrieved from vector database</span>
              </div>

              <div className="sources-grid">
                {ragResult.sources.map((src, i) => (
                  <div key={i} className="card source-card">
                    <div className="source-card-header">
                      <div className="source-meta">
                        <span className="source-index">#{i + 1}</span>
                        <span className="source-speaker">{src.speaker || 'Unknown Speaker'}</span>
                        {formatTimestamp(src.start_time, src.end_time) && (
                          <span className="source-time">
                            ⏱ {formatTimestamp(src.start_time, src.end_time)}
                          </span>
                        )}
                        <span className={`source-type-chip type-${src.source_type || 'transcript'}`}>
                          {src.source_type}
                        </span>
                      </div>
                      {src.score !== undefined && src.score !== null && (
                        <div className="source-score" title="Cosine Similarity Score">
                          {(src.score * 100).toFixed(0)}% match
                        </div>
                      )}
                    </div>

                    <div className="source-text">
                      <p>"{src.text}"</p>
                    </div>

                    <div className="source-footer">
                      <span className="source-meeting-name" title={src.meeting_id}>
                        📁 {src.filename || src.meeting_id}
                      </span>
                      {onSelectMeeting && src.meeting_id && (
                        <button
                          className="button-link"
                          onClick={() => onSelectMeeting(src.meeting_id)}
                        >
                          View Meeting →
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Semantic Search Results Display */}
      {searchMode === 'semantic' && semanticResults.length > 0 && !loading && (
        <div className="semantic-results-section" style={{ marginTop: '2rem' }}>
          <div className="sources-header">
            <h3 className="section-title">Matching Excerpts ({semanticResults.length})</h3>
            <span className="sources-subtitle">Ordered by vector cosine similarity</span>
          </div>

          <div className="sources-grid">
            {semanticResults.map((src, i) => (
              <div key={i} className="card source-card">
                <div className="source-card-header">
                  <div className="source-meta">
                    <span className="source-index">#{i + 1}</span>
                    <span className="source-speaker">{src.speaker || 'Speaker'}</span>
                    {formatTimestamp(src.start_time, src.end_time) && (
                      <span className="source-time">
                        ⏱ {formatTimestamp(src.start_time, src.end_time)}
                      </span>
                    )}
                    <span className={`source-type-chip type-${src.source_type || 'transcript'}`}>
                      {src.source_type}
                    </span>
                  </div>
                  {src.score !== undefined && (
                    <div className="source-score">{(src.score * 100).toFixed(0)}% match</div>
                  )}
                </div>

                <div className="source-text">
                  <p>"{src.text}"</p>
                </div>

                <div className="source-footer">
                  <span className="source-meeting-name">📁 {src.filename || src.meeting_id}</span>
                  {onSelectMeeting && src.meeting_id && (
                    <button className="button-link" onClick={() => onSelectMeeting(src.meeting_id)}>
                      View Meeting →
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
