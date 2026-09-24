import { useState, useRef } from 'react';

export default function UploadPage({ onViewMeeting, onGoToDashboard }) {
  const [file, setFile] = useState(null);
  const [autoProcess, setAutoProcess] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [status, setStatus] = useState(null); // { type: 'success' | 'error', message: string, meetingId?: string, isProcessing?: boolean }
  const fileInputRef = useRef(null);

  const handleDragOver = (e) => {
    e.preventDefault();
    e.currentTarget.classList.add('drag-active');
  };

  const handleDragLeave = (e) => {
    e.currentTarget.classList.remove('drag-active');
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.currentTarget.classList.remove('drag-active');
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      setFile(e.dataTransfer.files[0]);
      setStatus(null);
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      setFile(e.target.files[0]);
      setStatus(null);
    }
  };

  const handleUpload = async () => {
    if (!file) return;

    setUploading(true);
    setStatus(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      // 1. Upload audio file
      const response = await fetch('http://localhost:8000/meetings/upload', {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Upload failed');
      }

      const meetingId = data.meeting_id;
      let isProcessing = false;

      // 2. If auto-process is checked, trigger transcription immediately
      if (autoProcess) {
        try {
          const procRes = await fetch(`http://localhost:8000/meetings/${meetingId}/process`, {
            method: 'POST',
          });
          if (procRes.ok) {
            isProcessing = true;
          }
        } catch (procErr) {
          console.warn('Auto-process could not start automatically:', procErr);
        }
      }

      setStatus({
        type: 'success',
        message: isProcessing
          ? `Meeting uploaded successfully! Transcription & speaker diarization started in the background.`
          : `Meeting uploaded successfully! Ready for processing.`,
        meetingId: meetingId,
        isProcessing: isProcessing,
      });

      setFile(null);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    } catch (err) {
      setStatus({
        type: 'error',
        message: err.message || 'An error occurred during upload',
      });
    } finally {
      setUploading(false);
    }
  };

  return (
    <main className="card upload-card">
      <div className="upload-header">
        <h2 style={{ fontSize: '1.4rem', fontWeight: 700, letterSpacing: '-0.02em' }}>
          Upload Meeting Audio
        </h2>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', marginTop: '0.35rem' }}>
          Upload an audio or video recording to produce a speaker-attributed transcript and extract structured meeting intelligence.
        </p>
      </div>

      <div
        className="input-file-wrapper"
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
      >
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileChange}
          style={{ display: 'none' }}
          accept=".mp3,.wav,.m4a,.mp4"
        />

        {file ? (
          <div className="file-selected-box">
            <div className="file-icon">🎵</div>
            <p className="file-name">{file.name}</p>
            <p className="file-meta">
              {(file.size / (1024 * 1024)).toFixed(2)} MB • {file.type || 'audio file'}
            </p>
            <span className="file-change-hint">Click or drop to choose a different file</span>
          </div>
        ) : (
          <div>
            <div className="upload-icon-circle">
              <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                <polyline points="17 8 12 3 7 8"></polyline>
                <line x1="12" y1="3" x2="12" y2="15"></line>
              </svg>
            </div>
            <p style={{ color: 'var(--text-primary)', fontWeight: 600, marginTop: '1rem', fontSize: '1rem' }}>
              Click to browse or drag and drop audio file
            </p>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.8125rem', marginTop: '0.4rem' }}>
              Supported: MP3, WAV, M4A, or MP4 (Max size: 2 GB)
            </p>
          </div>
        )}
      </div>

      {/* Options Row */}
      <div className="upload-options">
        <label className="checkbox-label">
          <input
            type="checkbox"
            checked={autoProcess}
            onChange={(e) => setAutoProcess(e.target.checked)}
          />
          <span>Automatically start transcription & diarization immediately after upload</span>
        </label>
      </div>

      {/* Status Alerts */}
      {status && (
        <div className={status.type === 'error' ? 'alert-error' : 'alert-success'} style={{ marginTop: '1.5rem' }}>
          <p style={{ fontWeight: 500 }}>{status.message}</p>
          {status.type === 'success' && status.meetingId && onViewMeeting && (
            <div style={{ marginTop: '1rem', display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
              <button
                className="button-primary"
                onClick={() => onViewMeeting(status.meetingId)}
                style={{ fontSize: '0.875rem' }}
              >
                Open Meeting Details →
              </button>
              {onGoToDashboard && (
                <button
                  className="button-secondary"
                  onClick={onGoToDashboard}
                  style={{ fontSize: '0.875rem' }}
                >
                  View in Dashboard
                </button>
              )}
            </div>
          )}
        </div>
      )}

      {/* Actions */}
      <div className="upload-footer">
        {file && (
          <button
            className="button-secondary"
            onClick={() => { setFile(null); setStatus(null); }}
            disabled={uploading}
          >
            Clear
          </button>
        )}
        <button
          className="button-primary"
          onClick={handleUpload}
          disabled={!file || uploading}
          style={{ minWidth: '160px' }}
        >
          {uploading ? (
            <span style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem' }}>
              <span className="spinner-sm"></span> Uploading...
            </span>
          ) : autoProcess ? (
            'Upload & Process'
          ) : (
            'Upload Audio'
          )}
        </button>
      </div>
    </main>
  );
}
