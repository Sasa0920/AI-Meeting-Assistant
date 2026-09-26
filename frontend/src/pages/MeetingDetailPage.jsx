import { useState, useEffect, useCallback, useRef } from 'react';

export default function MeetingDetailPage({ meetingId: initialMeetingId, onBackToDashboard, onBackToUpload }) {
  const [meetingIdInput, setMeetingIdInput] = useState(initialMeetingId || '');
  const [meetingId, setMeetingId] = useState(initialMeetingId || '');
  const [activeTab, setActiveTab] = useState('intelligence'); // 'intelligence' | 'transcript' | 'raw'

  // Meeting Metadata
  const [meetingMeta, setMeetingMeta] = useState(null);
  const [metaLoading, setMetaLoading] = useState(false);

  // Intelligence State (Feature 3)
  const [intelligence, setIntelligence] = useState(null);
  const [intelStatus, setIntelStatus] = useState(null); // 'not_generated' | 'processing' | 'analyzed' | 'failed'
  const [intelLoading, setIntelLoading] = useState(false);
  const [triggeringIntel, setTriggeringIntel] = useState(false);

  // Transcript State (Feature 2)
  const [transcript, setTranscript] = useState(null);
  const [transcriptLoading, setTranscriptLoading] = useState(false);
  const [triggeringTranscript, setTriggeringTranscript] = useState(false);
  const [triggeringIndex, setTriggeringIndex] = useState(false);
  const [transcriptSearch, setTranscriptSearch] = useState('');
  const [selectedSpeakerFilter, setSelectedSpeakerFilter] = useState('ALL');

  // Interactive Action Items completed state (local toggle)
  const [completedTasks, setCompletedTasks] = useState({});

  // UI helpers
  const [error, setError] = useState(null);
  const [copiedSummary, setCopiedSummary] = useState(false);
  const [copiedReport, setCopiedReport] = useState(false);
  const [copiedId, setCopiedId] = useState(false);
  const pollIntervalRef = useRef(null);

  // 1. Fetch Meeting Metadata
  const fetchMeetingMeta = useCallback(async (id) => {
    if (!id) return null;
    try {
      const res = await fetch(`http://localhost:8000/meetings/${id}`);
      if (res.ok) {
        const data = await res.json();
        setMeetingMeta(data);
        return data;
      }
      return null;
    } catch (err) {
      console.error('Failed to fetch meeting meta:', err);
      return null;
    }
  }, []);

  // 2. Fetch Intelligence (Feature 3)
  const fetchIntelligence = useCallback(async (id) => {
    if (!id) return null;
    try {
      const res = await fetch(`http://localhost:8000/meetings/${id}/intelligence`);
      if (res.status === 404) {
        setIntelligence(null);
        setIntelStatus('not_generated');
        return null;
      }
      if (res.status === 500) {
        setIntelStatus('failed');
        setError('Intelligence processing failed on the server.');
        return null;
      }
      const data = await res.json();
      if (data.summary) {
        setIntelStatus('analyzed');
        setIntelligence(data);
        setError(null);
      } else {
        setIntelStatus(data.status);
      }
      return data;
    } catch (err) {
      console.error('Failed to fetch intelligence:', err);
      setError(err.message || 'Error fetching intelligence');
      return null;
    }
  }, []);

  // 3. Fetch Transcript (Feature 2)
  const fetchTranscript = useCallback(async (id) => {
    if (!id) return null;
    setTranscriptLoading(true);
    try {
      const res = await fetch(`http://localhost:8000/meetings/${id}/transcript`);
      if (res.ok) {
        const data = await res.json();
        if (data.transcript && data.transcript.length > 0) {
          setTranscript(data.transcript);
        }
        return data;
      }
      return null;
    } catch (err) {
      console.error('Failed to fetch transcript:', err);
      return null;
    } finally {
      setTranscriptLoading(false);
    }
  }, []);

  // Polling for live status updates
  useEffect(() => {
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current);
      pollIntervalRef.current = null;
    }

    const isProcessing =
      intelStatus === 'processing' ||
      (meetingMeta && meetingMeta.status === 'processing');

    if (isProcessing && meetingId) {
      pollIntervalRef.current = setInterval(async () => {
        const meta = await fetchMeetingMeta(meetingId);
        const intel = await fetchIntelligence(meetingId);
        if (meta && meta.has_transcript) {
          fetchTranscript(meetingId);
        }

        if (meta && meta.status !== 'processing' && intel && intel.status !== 'processing') {
          clearInterval(pollIntervalRef.current);
          pollIntervalRef.current = null;
        }
      }, 2500);
    }

    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
      }
    };
  }, [intelStatus, meetingMeta, meetingId, fetchMeetingMeta, fetchIntelligence, fetchTranscript]);

  // Load meeting data whenever meetingId changes
  useEffect(() => {
    if (!meetingId) return;
    setError(null);
    setMetaLoading(true);
    setIntelLoading(true);

    Promise.all([
      fetchMeetingMeta(meetingId),
      fetchIntelligence(meetingId),
      fetchTranscript(meetingId),
    ]).finally(() => {
      setMetaLoading(false);
      setIntelLoading(false);
    });
  }, [meetingId, fetchMeetingMeta, fetchIntelligence, fetchTranscript]);

  // Trigger Transcription (Feature 2)
  const handleTriggerTranscription = async () => {
    if (!meetingId) return;
    setTriggeringTranscript(true);
    setError(null);
    try {
      const res = await fetch(`http://localhost:8000/meetings/${meetingId}/process`, {
        method: 'POST',
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || 'Failed to start transcription');
      }
      await fetchMeetingMeta(meetingId);
    } catch (err) {
      setError(err.message || 'Failed to start transcription');
    } finally {
      setTriggeringTranscript(false);
    }
  };

  // Trigger Intelligence (Feature 3)
  const handleTriggerIntelligence = async () => {
    if (!meetingId) return;
    setTriggeringIntel(true);
    setError(null);
    try {
      const res = await fetch(`http://localhost:8000/meetings/${meetingId}/intelligence`, {
        method: 'POST',
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || 'Failed to trigger intelligence');
      }
      setIntelStatus('processing');
      await fetchMeetingMeta(meetingId);
    } catch (err) {
      setError(err.message || 'Failed to trigger intelligence');
    } finally {
      setTriggeringIntel(false);
    }
  };

  // Trigger Vector Indexing (Feature 4)
  const handleTriggerIndexing = async () => {
    if (!meetingId) return;
    setTriggeringIndex(true);
    setError(null);
    try {
      const res = await fetch(`http://localhost:8000/meetings/${meetingId}/index`, {
        method: 'POST',
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || 'Failed to trigger indexing');
      }
      await fetchMeetingMeta(meetingId);
    } catch (err) {
      setError(err.message || 'Failed to trigger indexing');
    } finally {
      setTriggeringIndex(false);
    }
  };

  // Copy Meeting ID
  const handleCopyId = () => {
    if (!meetingId) return;
    navigator.clipboard.writeText(meetingId);
    setCopiedId(true);
    setTimeout(() => setCopiedId(false), 2000);
  };

  // Copy Executive Summary
  const handleCopySummary = () => {
    if (!intelligence?.summary) return;
    navigator.clipboard.writeText(intelligence.summary);
    setCopiedSummary(true);
    setTimeout(() => setCopiedSummary(false), 2000);
  };

  // Copy Full Markdown Intelligence Report
  const handleCopyReport = () => {
    if (!intelligence) return;
    const lines = [
      `# Meeting Intelligence Report`,
      `**Meeting ID**: ${meetingId}`,
      `**Filename**: ${meetingMeta?.filename || 'Meeting'}`,
      ``,
      `## Executive Summary`,
      `${intelligence.summary}`,
      ``,
      `## Key Discussion Points`,
      ...(intelligence.key_points || []).map((p) => `- ${p}`),
      ``,
      `## Decisions Made`,
      ...(intelligence.decisions || []).map((d) => `- ${d}`),
      ``,
      `## Action Items`,
      ...(intelligence.action_items || []).map((a) => {
        const ass = a.assignee ? ` [@${a.assignee}]` : '';
        const dead = a.deadline ? ` (Due: ${a.deadline})` : '';
        return `- [ ] **${a.task}**${ass}${dead}`;
      }),
    ];
    navigator.clipboard.writeText(lines.join('\n'));
    setCopiedReport(true);
    setTimeout(() => setCopiedReport(false), 2000);
  };

  const toggleTaskCompleted = (idx) => {
    setCompletedTasks((prev) => ({
      ...prev,
      [idx]: !prev[idx],
    }));
  };

  const formatTimestamp = (seconds) => {
    if (seconds == null || isNaN(seconds)) return '00:00';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const getSpeakerClass = (speaker) => {
    if (!speaker) return 'spk-0';
    const num = speaker.replace(/\D/g, '');
    return num ? `spk-${num}` : 'spk-0';
  };

  // Filter transcript segments
  const uniqueSpeakers = Array.from(new Set((transcript || []).map((s) => s.speaker))).filter(Boolean);
  const filteredTranscript = (transcript || []).filter((seg) => {
    const matchesSearch = seg.text.toLowerCase().includes(transcriptSearch.toLowerCase());
    const matchesSpeaker = selectedSpeakerFilter === 'ALL' || seg.speaker === selectedSpeakerFilter;
    return matchesSearch && matchesSpeaker;
  });

  // If no meeting ID selected, render input prompt
  if (!meetingId) {
    return (
      <main className="card" style={{ maxWidth: '600px', margin: '0 auto' }}>
        <h2 style={{ fontSize: '1.35rem', fontWeight: 700, marginBottom: '0.75rem' }}>Look Up Meeting Details</h2>
        <p style={{ color: 'var(--text-secondary)', marginBottom: '1.5rem', fontSize: '0.9375rem' }}>
          Enter any meeting UUID to inspect its pipeline status, speaker-diarized transcript, and AI-generated summary and action items.
        </p>
        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <input
            type="text"
            placeholder="Paste meeting UUID..."
            value={meetingIdInput}
            onChange={(e) => setMeetingIdInput(e.target.value.trim())}
            style={{
              flex: 1,
              padding: '0.625rem 0.875rem',
              backgroundColor: 'var(--bg-tertiary)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--border-radius)',
              color: 'var(--text-primary)',
              fontFamily: 'inherit',
            }}
          />
          <button
            className="button-primary"
            onClick={() => setMeetingId(meetingIdInput)}
            disabled={!meetingIdInput}
          >
            Load Meeting
          </button>
        </div>
        <div style={{ marginTop: '1.5rem', display: 'flex', gap: '1rem' }}>
          {onBackToDashboard && (
            <button className="button-secondary" onClick={onBackToDashboard}>
              ← Go to Dashboard
            </button>
          )}
          {onBackToUpload && (
            <button className="button-secondary" onClick={onBackToUpload}>
              Upload New Audio
            </button>
          )}
        </div>
      </main>
    );
  }

  // Calculate Pipeline Stepper Statuses
  const isUploaded = true;
  const isTranscribing = meetingMeta?.status === 'processing' && !meetingMeta?.has_transcript;
  const isTranscribed = Boolean(meetingMeta?.has_transcript || (transcript && transcript.length > 0));
  const isAnalyzing = triggeringIntel || (intelStatus === 'processing' && !intelligence);
  const isAnalyzed = Boolean(intelligence || intelStatus === 'analyzed' || meetingMeta?.has_intelligence);
  const isIndexing = Boolean(triggeringIndex || (meetingMeta?.status === 'processing' && isTranscribed && !isAnalyzing));
  const isIndexed = Boolean(meetingMeta?.has_index || meetingMeta?.status === 'indexed');

  return (
    <div>
      {/* Top Header & Navigation */}
      <div className="detail-top-bar">
        <div className="detail-title-col">
          <div className="detail-breadcrumb">
            {onBackToDashboard && (
              <button className="btn-link" onClick={onBackToDashboard}>
                ← Dashboard
              </button>
            )}
            <span className="crumb-sep">/</span>
            <span className="crumb-current">Meeting Details</span>
          </div>

          <h2 className="detail-main-title">
            {meetingMeta?.filename || 'Meeting Recording'}
          </h2>

          <div className="detail-meta-row">
            <span className="meta-id-tag">
              ID: <code>{meetingId}</code>
              <button className="copy-btn-inline" onClick={handleCopyId}>
                {copiedId ? 'Copied' : 'Copy'}
              </button>
            </span>
            {meetingMeta?.upload_time && (
              <span className="meta-timestamp">
                Uploaded {new Date(meetingMeta.upload_time).toLocaleString()}
              </span>
            )}
          </div>
        </div>

        <div className="detail-actions-col">
          {/* Main Action Trigger Buttons */}
          {!isTranscribed && (
            <button
              className="button-primary"
              onClick={handleTriggerTranscription}
              disabled={isTranscribing || triggeringTranscript}
            >
              {isTranscribing || triggeringTranscript ? '◌ Transcribing...' : '▶ Start Transcription'}
            </button>
          )}

          {isTranscribed && (
            <button
              className="button-primary"
              onClick={handleTriggerIntelligence}
              disabled={isAnalyzing || triggeringIntel}
            >
              {isAnalyzing || triggeringIntel
                ? '◌ Analyzing...'
                : isAnalyzed
                ? '↻ Re-run Intelligence'
                : '✦ Extract Intelligence'}
            </button>
          )}

          {isAnalyzed && (
            <button className="button-secondary" onClick={handleCopyReport}>
              {copiedReport ? '✓ Report Copied!' : '📋 Copy Report (MD)'}
            </button>
          )}

          {isTranscribed && (
            <button
              className="button-primary"
              style={{ backgroundColor: isIndexed ? '#4f46e5' : undefined }}
              onClick={handleTriggerIndexing}
              disabled={isIndexing || triggeringIndex}
            >
              {isIndexing || triggeringIndex
                ? '◌ Indexing...'
                : isIndexed
                ? '✓ Re-index Knowledge Base'
                : '🔍 Index Knowledge Base'}
            </button>
          )}
        </div>
      </div>

      {/* Pipeline Progress Stepper */}
      <div className="pipeline-stepper-card">
        <div className="pipeline-stepper-track">
          {/* Step 1: Upload */}
          <div className="stepper-step completed">
            <div className="step-circle">✓</div>
            <div className="step-info">
              <div className="step-num">Step 1</div>
              <div className="step-name">Audio Ingestion</div>
              <div className="step-status">File Uploaded</div>
            </div>
          </div>

          <div className={`stepper-connector ${isTranscribed ? 'completed' : isTranscribing ? 'active' : ''}`} />

          {/* Step 2: Transcription & Diarization */}
          <div className={`stepper-step ${isTranscribed ? 'completed' : isTranscribing ? 'active' : ''}`}>
            <div className="step-circle">
              {isTranscribed ? '✓' : isTranscribing ? '◌' : '2'}
            </div>
            <div className="step-info">
              <div className="step-num">Step 2</div>
              <div className="step-name">Transcription & Diarization</div>
              <div className="step-status">
                {isTranscribed
                  ? 'Transcribed'
                  : isTranscribing
                  ? 'Transcribing audio...'
                  : 'Pending'}
              </div>
            </div>
          </div>

          <div className={`stepper-connector ${isAnalyzed ? 'completed' : isAnalyzing ? 'active' : ''}`} />

          {/* Step 3: Meeting Intelligence */}
          <div className={`stepper-step ${isAnalyzed ? 'completed' : isAnalyzing ? 'active' : ''}`}>
            <div className="step-circle">
              {isAnalyzed ? '✦' : isAnalyzing ? '◌' : '3'}
            </div>
            <div className="step-info">
              <div className="step-num">Step 3</div>
              <div className="step-name">Meeting Intelligence</div>
              <div className="step-status">
                {isAnalyzed
                  ? 'Analyzed'
                  : isAnalyzing
                  ? 'Extracting with Gemini...'
                  : isTranscribed
                  ? 'Ready for Analysis'
                  : 'Waiting for Step 2'}
              </div>
            </div>
          </div>

          <div className={`stepper-connector ${isIndexed ? 'completed' : isIndexing ? 'active' : ''}`} />

          {/* Step 4: Vector Knowledge Base */}
          <div className={`stepper-step ${isIndexed ? 'completed' : isIndexing ? 'active' : ''}`}>
            <div className="step-circle">
              {isIndexed ? '🔍' : isIndexing ? '◌' : '4'}
            </div>
            <div className="step-info">
              <div className="step-num">Step 4</div>
              <div className="step-name">Knowledge Base & RAG</div>
              <div className="step-status">
                {isIndexed
                  ? 'Indexed in Qdrant'
                  : isIndexing
                  ? 'Vectorizing...'
                  : isTranscribed
                  ? 'Ready to Index'
                  : 'Waiting for Step 2'}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Error Banner */}
      {error && <div className="alert-error" style={{ marginBottom: '1.5rem' }}>{error}</div>}

      {/* Section Tabs */}
      <div className="section-tabs">
        <button
          className={`tab-button ${activeTab === 'intelligence' ? 'active' : ''}`}
          onClick={() => setActiveTab('intelligence')}
        >
          ✦ Intelligence & Action Items
          {intelligence?.action_items && (
            <span className="tab-pill">{intelligence.action_items.length} tasks</span>
          )}
        </button>

        <button
          className={`tab-button ${activeTab === 'transcript' ? 'active' : ''}`}
          onClick={() => setActiveTab('transcript')}
        >
          🎙 Speaker Transcript
          {transcript && transcript.length > 0 && (
            <span className="tab-pill">{transcript.length} turns</span>
          )}
        </button>

        <button
          className={`tab-button ${activeTab === 'raw' ? 'active' : ''}`}
          onClick={() => setActiveTab('raw')}
        >
          {'{ }'} Raw JSON
        </button>
      </div>

      {/* TAB 1: Feature 3 Intelligence View */}
      {activeTab === 'intelligence' && (
        <div className="tab-content">
          {intelLoading ? (
            <div className="card loading-state-card">
              <div className="loading-spinner"></div>
              <p>Loading meeting intelligence...</p>
            </div>
          ) : isAnalyzing ? (
            <div className="card processing-banner">
              <div className="pulsing-ai-badge">✦</div>
              <h3 style={{ fontSize: '1.15rem', fontWeight: 600, marginTop: '0.75rem' }}>
                Extracting Meeting Intelligence via Gemini...
              </h3>
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', marginTop: '0.4rem', maxWidth: '500px', margin: '0.4rem auto 0' }}>
                Analyzing dialogue flow, extracting key discussion points, isolating agreed decisions, and identifying assigned action items with deadlines.
              </p>
            </div>
          ) : !isTranscribed ? (
            <div className="card empty-intel-card">
              <div className="empty-intel-icon">🎙</div>
              <h3 style={{ fontSize: '1.125rem', fontWeight: 600, marginBottom: '0.5rem' }}>
                Transcript Not Ready
              </h3>
              <p style={{ color: 'var(--text-secondary)', maxWidth: '440px', margin: '0 auto 1.5rem', fontSize: '0.875rem' }}>
                Feature 3 requires speaker-attributed text from Step 2. Run the transcription stage first to generate the meeting transcript.
              </p>
              <button
                className="button-primary"
                onClick={handleTriggerTranscription}
                disabled={isTranscribing || triggeringTranscript}
              >
                {isTranscribing || triggeringTranscript ? 'Transcribing...' : 'Run Transcription Now'}
              </button>
            </div>
          ) : !intelligence ? (
            <div className="card empty-intel-card">
              <div className="empty-intel-icon">✦</div>
              <h3 style={{ fontSize: '1.15rem', fontWeight: 600, marginBottom: '0.5rem' }}>
                Ready to Extract Intelligence
              </h3>
              <p style={{ color: 'var(--text-secondary)', maxWidth: '480px', margin: '0 auto 1.5rem', fontSize: '0.875rem' }}>
                Speaker transcript is available ({transcript?.length || 0} turns). Click below to generate an executive summary, main discussion topics, decisions, and action items in a single LLM pass.
              </p>
              <button
                className="button-primary"
                onClick={handleTriggerIntelligence}
                disabled={triggeringIntel}
              >
                {triggeringIntel ? 'Starting Analysis...' : '✦ Extract Meeting Intelligence'}
              </button>
            </div>
          ) : (
            <div className="intelligence-grid">
              {/* 1. Executive Summary */}
              <section className="intel-section">
                <div className="intel-section-header">
                  <h3 className="section-title">
                    <span className="section-icon">📝</span>
                    Executive Summary
                  </h3>
                  <button className="copy-btn-inline" onClick={handleCopySummary}>
                    {copiedSummary ? '✓ Copied!' : 'Copy Summary'}
                  </button>
                </div>
                <div className="summary-card">
                  <p className="summary-text">{intelligence.summary}</p>
                </div>
              </section>

              {/* 2. Key Discussion Points */}
              {intelligence.key_points && intelligence.key_points.length > 0 && (
                <section className="intel-section">
                  <h3 className="section-title">
                    <span className="section-icon">💡</span>
                    Key Discussion Points ({intelligence.key_points.length})
                  </h3>
                  <div className="key-points-grid">
                    {intelligence.key_points.map((point, idx) => (
                      <div key={idx} className="key-point-card">
                        <span className="key-point-num">{idx + 1}</span>
                        <p className="key-point-text">{point}</p>
                      </div>
                    ))}
                  </div>
                </section>
              )}

              {/* 3. Decisions Made */}
              {intelligence.decisions && intelligence.decisions.length > 0 && (
                <section className="intel-section">
                  <h3 className="section-title">
                    <span className="section-icon">⚖️</span>
                    Decisions Made ({intelligence.decisions.length})
                  </h3>
                  <div className="decisions-list">
                    {intelligence.decisions.map((decision, idx) => (
                      <div key={idx} className="decision-card">
                        <div className="decision-badge">Agreed Decision</div>
                        <p className="decision-content">{decision}</p>
                      </div>
                    ))}
                  </div>
                </section>
              )}

              {/* 4. Action Items */}
              <section className="intel-section">
                <div className="intel-section-header">
                  <h3 className="section-title">
                    <span className="section-icon">✅</span>
                    Action Items ({intelligence.action_items?.length || 0})
                  </h3>
                  <span className="action-hint">Click checkbox to mark done</span>
                </div>

                {!intelligence.action_items || intelligence.action_items.length === 0 ? (
                  <div className="card" style={{ padding: '1.5rem', textAlign: 'center', color: 'var(--text-secondary)' }}>
                    No explicit action items were assigned in this meeting.
                  </div>
                ) : (
                  <div className="action-items-grid">
                    {intelligence.action_items.map((item, idx) => {
                      const isDone = Boolean(completedTasks[idx]);
                      return (
                        <div
                          key={idx}
                          className={`action-card ${isDone ? 'completed-task' : ''}`}
                          onClick={() => toggleTaskCompleted(idx)}
                        >
                          <div className="action-checkbox-col">
                            <div className={`custom-checkbox ${isDone ? 'checked' : ''}`}>
                              {isDone && '✓'}
                            </div>
                          </div>

                          <div className="action-body-col">
                            <div className={`action-task-title ${isDone ? 'line-through' : ''}`}>
                              {item.task}
                            </div>

                            <div className="action-tags-row">
                              {item.assignee ? (
                                <span className="action-tag assignee" title="Assigned person">
                                  👤 {item.assignee}
                                </span>
                              ) : (
                                <span className="action-tag unassigned" title="No specific assignee">
                                  👤 Unassigned
                                </span>
                              )}

                              {item.deadline ? (
                                <span className="action-tag deadline" title="Due deadline">
                                  📅 {item.deadline}
                                </span>
                              ) : (
                                <span className="action-tag no-deadline" title="No explicit deadline mentioned">
                                  📅 No deadline
                                </span>
                              )}
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </section>
            </div>
          )}
        </div>
      )}

      {/* TAB 2: Feature 2 Speaker Transcript View */}
      {activeTab === 'transcript' && (
        <div className="tab-content">
          {transcriptLoading ? (
            <div className="card loading-state-card">
              <div className="loading-spinner"></div>
              <p>Loading speaker-attributed transcript...</p>
            </div>
          ) : !transcript || transcript.length === 0 ? (
            <div className="card empty-intel-card">
              <div className="empty-intel-icon">🎙</div>
              <h3 style={{ fontSize: '1.125rem', fontWeight: 600, marginBottom: '0.5rem' }}>
                No Transcript Generated Yet
              </h3>
              <p style={{ color: 'var(--text-secondary)', maxWidth: '440px', margin: '0 auto 1.5rem', fontSize: '0.875rem' }}>
                Run speech-to-text and speaker diarization to separate speech by speaker and align words with timestamps.
              </p>
              <button
                className="button-primary"
                onClick={handleTriggerTranscription}
                disabled={isTranscribing || triggeringTranscript}
              >
                {isTranscribing || triggeringTranscript ? 'Transcribing...' : 'Run Transcription'}
              </button>
            </div>
          ) : (
            <div className="card transcript-card">
              {/* Transcript Search & Speaker Filter */}
              <div className="transcript-toolbar">
                <div className="search-box" style={{ flex: 1, minWidth: '220px' }}>
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <circle cx="11" cy="11" r="8"></circle>
                    <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
                  </svg>
                  <input
                    type="text"
                    placeholder="Search in transcript..."
                    value={transcriptSearch}
                    onChange={(e) => setTranscriptSearch(e.target.value)}
                  />
                  {transcriptSearch && (
                    <button className="clear-search" onClick={() => setTranscriptSearch('')}>✕</button>
                  )}
                </div>

                <div className="speaker-filters">
                  <button
                    className={`filter-pill ${selectedSpeakerFilter === 'ALL' ? 'active' : ''}`}
                    onClick={() => setSelectedSpeakerFilter('ALL')}
                  >
                    All ({transcript.length})
                  </button>
                  {uniqueSpeakers.map((spk) => (
                    <button
                      key={spk}
                      className={`filter-pill ${selectedSpeakerFilter === spk ? 'active' : ''}`}
                      onClick={() => setSelectedSpeakerFilter(spk)}
                    >
                      {spk}
                    </button>
                  ))}
                </div>
              </div>

              {/* Transcript Dialogue List */}
              <div className="transcript-stream">
                {filteredTranscript.length === 0 ? (
                  <p style={{ color: 'var(--text-secondary)', textAlign: 'center', padding: '2rem 0' }}>
                    No segments match your search or filter.
                  </p>
                ) : (
                  filteredTranscript.map((seg, idx) => (
                    <div key={idx} className="transcript-row">
                      <div className="transcript-gutter">
                        <span className={`speaker-badge ${getSpeakerClass(seg.speaker)}`}>
                          {seg.speaker}
                        </span>
                        <span className="timestamp-badge">
                          {formatTimestamp(seg.start)} – {formatTimestamp(seg.end)}
                        </span>
                      </div>
                      <div className="transcript-text-content">
                        {seg.text}
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {/* TAB 3: Raw JSON */}
      {activeTab === 'raw' && (
        <div className="tab-content">
          <div className="card raw-json-card">
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '1rem' }}>
              <h3 style={{ fontSize: '1rem', fontWeight: 600 }}>Raw API Payloads</h3>
              <button
                className="button-secondary"
                onClick={() => {
                  navigator.clipboard.writeText(
                    JSON.stringify({ metadata: meetingMeta, intelligence, transcript }, null, 2)
                  );
                }}
              >
                Copy JSON
              </button>
            </div>
            <pre className="code-block">
              {JSON.stringify({ metadata: meetingMeta, intelligence, transcript }, null, 2)}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
}
