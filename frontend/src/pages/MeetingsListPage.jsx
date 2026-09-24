import { useState, useEffect } from 'react';

export default function MeetingsListPage({ onSelectMeeting, onGoToUpload }) {
  const [meetings, setMeetings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [copiedId, setCopiedId] = useState(null);

  const fetchMeetings = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch('http://localhost:8000/meetings');
      if (!res.ok) {
        throw new Error('Failed to load meetings list');
      }
      const data = await res.json();
      setMeetings(data);
    } catch (err) {
      console.error('Error loading meetings:', err);
      setError(err.message || 'Could not connect to backend server');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMeetings();
  }, []);

  const handleCopyId = (e, id) => {
    e.stopPropagation();
    navigator.clipboard.writeText(id);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '—';
    try {
      const d = new Date(dateStr);
      return d.toLocaleDateString(undefined, {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return dateStr;
    }
  };

  const filteredMeetings = meetings.filter((m) => {
    const q = searchQuery.toLowerCase();
    return (
      m.filename.toLowerCase().includes(q) ||
      m.id.toLowerCase().includes(q) ||
      m.status.toLowerCase().includes(q)
    );
  });

  const getStatusBadge = (status) => {
    switch (status) {
      case 'analyzed':
        return <span className="badge badge-analyzed">● Analyzed</span>;
      case 'done':
        return <span className="badge badge-done">● Transcribed</span>;
      case 'processing':
        return <span className="badge badge-processing">◌ Processing...</span>;
      case 'uploaded':
        return <span className="badge badge-uploaded">● Uploaded</span>;
      case 'failed':
        return <span className="badge badge-failed">✕ Failed</span>;
      default:
        return <span className="badge">{status}</span>;
    }
  };

  const totalMeetings = meetings.length;
  const analyzedCount = meetings.filter((m) => m.status === 'analyzed' || m.has_intelligence).length;
  const transcribedCount = meetings.filter((m) => m.has_transcript).length;

  return (
    <div>
      {/* Header & Stats Banner */}
      <div className="dashboard-header">
        <div>
          <h2 style={{ fontSize: '1.5rem', fontWeight: 700, letterSpacing: '-0.02em', color: 'var(--text-primary)' }}>
            Meetings Dashboard
          </h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', marginTop: '0.25rem' }}>
            Monitor and manage your meeting audio recordings, speaker transcripts, and AI summaries.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <button className="button-secondary" onClick={fetchMeetings} title="Refresh meetings">
            ↻ Refresh
          </button>
          <button className="button-primary" onClick={onGoToUpload}>
            + Upload Meeting
          </button>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-label">Total Meetings</div>
          <div className="stat-value">{totalMeetings}</div>
          <div className="stat-desc">Audio files ingested</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Transcribed</div>
          <div className="stat-value">{transcribedCount}</div>
          <div className="stat-desc">Diarized speaker segments</div>
        </div>
        <div className="stat-card highlight">
          <div className="stat-label">Intelligence Analyzed</div>
          <div className="stat-value" style={{ color: 'var(--accent-teal)' }}>{analyzedCount}</div>
          <div className="stat-desc">Summaries & action items extracted</div>
        </div>
      </div>

      {/* Filter / Search Bar */}
      <div className="meeting-filter-bar">
        <div className="search-box">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="11" cy="11" r="8"></circle>
            <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
          </svg>
          <input
            type="text"
            placeholder="Search meetings by filename, ID, or status..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
          {searchQuery && (
            <button className="clear-search" onClick={() => setSearchQuery('')}>✕</button>
          )}
        </div>
      </div>

      {/* Error state */}
      {error && (
        <div className="alert-error" style={{ marginBottom: '1.5rem' }}>
          <p>{error}</p>
          <button className="button-secondary" onClick={fetchMeetings} style={{ marginTop: '0.5rem', fontSize: '0.8125rem' }}>
            Try Again
          </button>
        </div>
      )}

      {/* Loading state */}
      {loading ? (
        <div className="card" style={{ textAlign: 'center', padding: '3.5rem 1.5rem' }}>
          <div className="loading-spinner"></div>
          <p style={{ color: 'var(--text-secondary)', marginTop: '1rem' }}>Loading meetings list...</p>
        </div>
      ) : filteredMeetings.length === 0 ? (
        <div className="card empty-dashboard">
          <div className="empty-icon">📁</div>
          <h3 style={{ fontSize: '1.125rem', fontWeight: 600, marginBottom: '0.5rem' }}>
            {searchQuery ? 'No matching meetings found' : 'No meetings yet'}
          </h3>
          <p style={{ color: 'var(--text-secondary)', maxWidth: '420px', margin: '0 auto 1.5rem', fontSize: '0.875rem' }}>
            {searchQuery
              ? `No meetings match "${searchQuery}". Try a different keyword.`
              : 'Upload your first meeting recording (MP3, WAV, M4A) to automatically transcribe and extract AI intelligence.'}
          </p>
          {!searchQuery && (
            <button className="button-primary" onClick={onGoToUpload}>
              Upload Meeting Recording
            </button>
          )}
        </div>
      ) : (
        /* Meetings List Grid / Table */
        <div className="meetings-list">
          {filteredMeetings.map((m) => (
            <div
              key={m.id}
              className="meeting-row-card"
              onClick={() => onSelectMeeting(m.id)}
            >
              <div className="meeting-row-main">
                <div className="meeting-icon-box">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"></path>
                    <path d="M19 10v2a7 7 0 0 1-14 0v-2"></path>
                    <line x1="12" y1="19" x2="12" y2="22"></line>
                  </svg>
                </div>

                <div className="meeting-row-info">
                  <div className="meeting-row-title-bar">
                    <h3 className="meeting-title">{m.filename}</h3>
                    {getStatusBadge(m.status)}
                  </div>

                  <div className="meeting-row-meta">
                    <span className="meta-time">Uploaded {formatDate(m.upload_time)}</span>
                    <span className="meta-sep">•</span>
                    <span className="meta-id">
                      ID: <code>{m.id.substring(0, 8)}...</code>
                      <button
                        className="copy-btn-inline"
                        onClick={(e) => handleCopyId(e, m.id)}
                        title="Copy meeting UUID"
                      >
                        {copiedId === m.id ? 'Copied' : 'Copy'}
                      </button>
                    </span>
                  </div>
                </div>
              </div>

              <div className="meeting-row-pipeline-status">
                <div className="pipeline-chips">
                  <span className={`pipe-chip ${m.has_transcript ? 'active' : ''}`}>
                    {m.has_transcript ? '✓ Transcript' : '○ Transcript'}
                  </span>
                  <span className={`pipe-chip ${m.has_intelligence ? 'active-ai' : ''}`}>
                    {m.has_intelligence ? '✦ Intelligence' : '○ Intelligence'}
                  </span>
                </div>

                <button className="button-primary-ghost" onClick={() => onSelectMeeting(m.id)}>
                  View Details →
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
