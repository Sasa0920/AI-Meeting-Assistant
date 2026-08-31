import './index.css';
import UploadPage from './pages/UploadPage';

function App() {
  return (
    <div style={{ maxWidth: '800px', margin: '4rem auto', padding: '0 1rem' }}>
      <header style={{ marginBottom: '3rem' }}>
        <h1 style={{ fontWeight: 600, fontSize: '1.5rem', marginBottom: '0.5rem' }}>AI Meeting Assistant</h1>
        <p style={{ color: 'var(--text-secondary)' }}>Upload your meeting recording to get started.</p>
      </header>

      {/* 
        For now we just render the UploadPage. 
        As we add more features, we can add a router here to switch between screens
        like Dashboard, Meeting Detail, and Search/Ask.
      */}
      <UploadPage />
    </div>
  );
}

export default App;
