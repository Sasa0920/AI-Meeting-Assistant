import { useState, useEffect } from 'react';
import './index.css';
import MeetingsListPage from './pages/MeetingsListPage';
import UploadPage from './pages/UploadPage';
import MeetingDetailPage from './pages/MeetingDetailPage';

function App() {
  const getInitialMeetingId = () => {
    const hash = window.location.hash.replace('#', '');
    if (hash.startsWith('meeting=')) {
      return hash.split('=')[1] || '';
    }
    const params = new URLSearchParams(window.location.search);
    return params.get('meetingId') || '';
  };

  const initialId = getInitialMeetingId();
  const [currentScreen, setCurrentScreen] = useState(initialId ? 'detail' : 'dashboard'); // 'dashboard' | 'upload' | 'detail'
  const [selectedMeetingId, setSelectedMeetingId] = useState(initialId);

  useEffect(() => {
    const handleHashChange = () => {
      const id = getInitialMeetingId();
      if (id) {
        setSelectedMeetingId(id);
        setCurrentScreen('detail');
      } else if (!window.location.hash) {
        // No hash, default to dashboard
      }
    };
    window.addEventListener('hashchange', handleHashChange);
    return () => window.removeEventListener('hashchange', handleHashChange);
  }, []);

  const handleSelectMeeting = (id) => {
    setSelectedMeetingId(id);
    setCurrentScreen('detail');
    window.location.hash = `meeting=${id}`;
  };

  const handleGoToDashboard = () => {
    setCurrentScreen('dashboard');
    if (window.location.hash) {
      window.history.replaceState(null, '', window.location.pathname);
    }
  };

  const handleGoToUpload = () => {
    setCurrentScreen('upload');
    if (window.location.hash) {
      window.history.replaceState(null, '', window.location.pathname);
    }
  };

  const handleGoToDetail = () => {
    setCurrentScreen('detail');
  };

  return (
    <div className="app-container">
      {/* App Header Navigation */}
      <header className="app-header">
        <div className="app-brand" onClick={handleGoToDashboard} style={{ cursor: 'pointer' }}>
          <div className="brand-logo-badge">✦</div>
          <div>
            <h1 className="brand-title">AI Meeting Assistant</h1>
            <p className="brand-subtitle">
              Audio Ingestion • Diarization • Gemini Intelligence
            </p>
          </div>
        </div>

        <nav className="nav-links">
          <button
            className={`nav-button ${currentScreen === 'dashboard' ? 'active' : ''}`}
            onClick={handleGoToDashboard}
          >
            Dashboard
          </button>
          <button
            className={`nav-button ${currentScreen === 'upload' ? 'active' : ''}`}
            onClick={handleGoToUpload}
          >
            + Upload
          </button>
          <button
            className={`nav-button ${currentScreen === 'detail' ? 'active' : ''}`}
            onClick={handleGoToDetail}
          >
            Meeting Detail {selectedMeetingId ? `(${selectedMeetingId.slice(0, 6)}...)` : ''}
          </button>
        </nav>
      </header>

      {/* Screen Content */}
      <main className="app-main-content">
        {currentScreen === 'dashboard' && (
          <MeetingsListPage
            onSelectMeeting={handleSelectMeeting}
            onGoToUpload={handleGoToUpload}
          />
        )}

        {currentScreen === 'upload' && (
          <UploadPage
            onViewMeeting={handleSelectMeeting}
            onGoToDashboard={handleGoToDashboard}
          />
        )}

        {currentScreen === 'detail' && (
          <MeetingDetailPage
            meetingId={selectedMeetingId}
            onBackToDashboard={handleGoToDashboard}
            onBackToUpload={handleGoToUpload}
          />
        )}
      </main>

      <footer className="app-footer">
        <p>AI Meeting Assistant • Built with Whisper, Pyannote & Gemini Flash</p>
      </footer>
    </div>
  );
}

export default App;
