import { useState, useRef } from 'react';

export default function UploadPage() {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [status, setStatus] = useState(null); // { type: 'success' | 'error', message: string }
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
      // Backend URL running on localhost:8000
      const response = await fetch('http://localhost:8000/meetings/upload', {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Upload failed');
      }

      setStatus({
        type: 'success',
        message: `Meeting uploaded successfully! ID: ${data.meeting_id}`
      });
      setFile(null);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    } catch (err) {
      setStatus({
        type: 'error',
        message: err.message || 'An error occurred during upload'
      });
    } finally {
      setUploading(false);
    }
  };

  return (
    <main className="card">
      <h2 style={{ fontSize: '1.25rem', fontWeight: 500, marginBottom: '1.5rem' }}>Upload Meeting</h2>
      
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
          <div>
            <p style={{ fontWeight: 500, color: 'var(--accent-teal)' }}>{file.name}</p>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', marginTop: '0.5rem' }}>
              {(file.size / (1024 * 1024)).toFixed(2)} MB
            </p>
          </div>
        ) : (
          <div>
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="var(--text-secondary)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ marginBottom: '1rem' }}>
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
              <polyline points="17 8 12 3 7 8"></polyline>
              <line x1="12" y1="3" x2="12" y2="15"></line>
            </svg>
            <p style={{ color: 'var(--text-primary)' }}>Click to upload or drag and drop</p>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', marginTop: '0.5rem' }}>MP3, WAV, M4A, or MP4 (Max 2GB)</p>
          </div>
        )}
      </div>

      {status && (
        <div className={status.type === 'error' ? 'alert-error' : 'alert-success'}>
          {status.message}
        </div>
      )}

      <div style={{ marginTop: '2rem', display: 'flex', justifyContent: 'flex-end', gap: '1rem' }}>
        {file && (
          <button 
            className="button-secondary"
            onClick={() => { setFile(null); setStatus(null); }}
            disabled={uploading}
          >
            Cancel
          </button>
        )}
        <button 
          className="button-primary"
          onClick={handleUpload}
          disabled={!file || uploading}
        >
          {uploading ? 'Uploading...' : 'Process Meeting'}
        </button>
      </div>
    </main>
  );
}
