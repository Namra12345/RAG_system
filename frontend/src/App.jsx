import React, { useState, useEffect } from 'react';

function App() {
  const [text, setText] = useState('');
  const [query, setQuery] = useState('');
  const [results, setResults] = useState({ answer: '', sources: [] });
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [sessionId, setSessionId] = useState('');

  // Generates a bulletproof session ID fallback string that never crashes on local dev servers
  useEffect(() => {
    const generateSafeId = () => {
      return Math.random().toString(36).substring(2, 15) + 
             Math.random().toString(36).substring(2, 15);
    };
    setSessionId(generateSafeId());
  }, []);

  // Automatically shifts between localhost (testing) and your EC2 Public IP (production)
  const API_URL = window.location.hostname === 'localhost' 
    ? 'http://localhost:8000' 
    : `http://${window.location.hostname}:8000`;

  const handleUpload = async () => {
    if (!text.trim()) return;
    setUploading(true);
    setMessage('Processing & vectorizing text...');
    try {
      const res = await fetch(`${API_URL}/upload`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text, session_id: sessionId })
      });
      const data = await res.json();
      if (res.ok) {
        setMessage('✨ Context successfully isolated to your current session!');
        setText('');
      } else {
        setMessage(`❌ Error: ${data.detail || 'Failed to upload'}`);
      }
    } catch (err) {
      setMessage('❌ Error connecting to backend server.');
    } finally {
      setUploading(false);
    }
  };

  const handleSearch = async () => {
    if (!query.trim()) return;
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: query, session_id: sessionId })
      });
      const data = await res.json();
      if (res.ok) {
        setResults({
          answer: data.answer,
          sources: data.sources || []
        });
      } else {
        alert(`Backend Error: ${data.detail}`);
      }
    } catch (err) {
      alert('Error fetching answers from backend.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ backgroundColor: '#f8fafc', minHeight: '100vh', padding: '40px 20px', fontFamily: '"Inter", system-ui, -apple-system, sans-serif', color: '#1e293b' }}>
      <div style={{ maxWidth: '750px', margin: '0 auto' }}>
        
        {/* Header Block */}
        <header style={{ textAlign: 'center', marginBottom: '40px' }}>
          <h1 style={{ fontSize: '32px', fontWeight: '800', tracking: '-0.025em', color: '#0f172a', margin: '0 0 8px 0' }}>
            ⚡ Light-RAG Sandbox
          </h1>
          <p style={{ fontSize: '15px', color: '#64748b', margin: 0, fontWeight: '500' }}>
            Gemini 2.5 Flash + Qdrant Cloud Cluster Engine
          </p>
          <div style={{ display: 'inline-block', marginTop: '14px', padding: '6px 12px', backgroundColor: '#e2e8f0', borderRadius: '20px', fontSize: '12px', fontWeight: '600', color: '#475569' }}>
            Session Active: <span style={{ fontFamily: 'monospace', color: '#2563eb' }}>{sessionId ? sessionId.substring(0, 8) + '...' : 'initializing'}</span>
          </div>
        </header>

        {/* Section 1: Data Ingestion Card */}
        <div style={{ backgroundColor: '#ffffff', border: '1px solid #e2e8f0', padding: '28px', borderRadius: '16px', boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03)', marginBottom: '28px' }}>
          <h3 style={{ marginTop: 0, fontSize: '18px', fontWeight: '700', color: '#334155', marginBottom: '6px' }}>
            1. Ingest Factual Context
          </h3>
          <p style={{ fontSize: '13px', color: '#64748b', marginTop: 0, marginBottom: '16px' }}>
            Every browser tab fresh-start builds an isolated environment. Data inputted here is completely secure to this tab session.
          </p>
          <textarea 
            style={{ width: '100%', height: '110px', padding: '14px', boxSizing: 'border-box', borderRadius: '8px', border: '1px solid #cbd5e1', fontSize: '14px', lineHeight: '1.5', outline: 'none', transition: 'border-color 0.2s', fontFamily: 'inherit' }} 
            value={text} 
            onChange={(e) => setText(e.target.value)} 
            placeholder="Paste raw text, knowledge updates, proprietary logs, or internal procedures..." 
          />
          <button 
            style={{ marginTop: '14px', padding: '12px 24px', backgroundColor: '#2563eb', color: '#ffffff', border: 'none', borderRadius: '8px', cursor: text.trim() ? 'pointer' : 'not-allowed', fontWeight: '600', fontSize: '14px', opacity: text.trim() && !uploading ? 1 : 0.6, transition: 'all 0.2s', boxShadow: '0 2px 4px rgba(37, 99, 235, 0.2)' }} 
            onClick={handleUpload}
            disabled={!text.trim() || uploading}
          >
            {uploading ? 'Vectorizing...' : 'Upload & Train Database'}
          </button>
          
          {message && (
            <div style={{ display: 'flex', alignItems: 'center', backgroundColor: message.includes('❌') ? '#fef2f2' : '#f0f9ff', padding: '12px 16px', borderRadius: '8px', marginTop: '16px', borderLeft: `4px solid ${message.includes('❌') ? '#ef4444' : '#0284c7'}` }}>
              <span style={{ fontSize: '14px', fontWeight: '500', color: message.includes('❌') ? '#991b1b' : '#0369a1' }}>{message}</span>
            </div>
          )}
        </div>

        {/* Section 2: Retrieval UI Card */}
        <div style={{ backgroundColor: '#ffffff', border: '1px solid #e2e8f0', padding: '28px', borderRadius: '16px', boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03)' }}>
          <h3 style={{ marginTop: 0, fontSize: '18px', fontWeight: '700', color: '#334155', marginBottom: '16px' }}>
            2. Run Real-Time Pipeline Queries
          </h3>
          <div style={{ display: 'flex', gap: '12px' }}>
            <input 
              style={{ flex: 1, padding: '14px', borderRadius: '8px', border: '1px solid #cbd5e1', fontSize: '14px', outline: 'none' }} 
              type="text" 
              value={query} 
              onChange={(e) => setQuery(e.target.value)} 
              placeholder="Ask questions restricted to your session dataset rules..." 
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
            />
            <button 
              style={{ padding: '0 28px', backgroundColor: '#10b981', color: '#ffffff', border: 'none', borderRadius: '8px', cursor: query.trim() ? 'pointer' : 'not-allowed', fontWeight: '600', fontSize: '14px', opacity: query.trim() && !loading ? 1 : 0.6, transition: 'all 0.2s', boxShadow: '0 2px 4px rgba(16, 185, 129, 0.2)' }} 
              onClick={handleSearch}
              disabled={!query.trim() || loading}
            >
              {loading ? 'Analyzing...' : 'Query'}
            </button>
          </div>

          {/* AI Response Display Area */}
          <h4 style={{ marginTop: '32px', marginBottom: '10px', fontSize: '15px', fontWeight: '700', color: '#475569', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            🤖 AI Synthesis Output
          </h4>
          
          {results.answer ? (
            <div style={{ backgroundColor: '#f5f3ff', padding: '20px', borderRadius: '10px', borderLeft: '4px solid #7c3aed', marginBottom: '24px', lineHeight: '1.6', fontSize: '15px', color: '#4c1d95', fontWeight: '500' }}>
              {results.answer}
            </div>
          ) : (
            <div style={{ padding: '20px', textAlign: 'center', border: '2px dashed #e2e8f0', borderRadius: '10px', color: '#94a3b8', fontSize: '14px', marginBottom: '24px' }}>
              No answers generated yet. Feed input context above, then execute a prompt payload query.
            </div>
          )}

          {/* Context Sources Attribution Box */}
          {results.sources.length > 0 && (
            <div style={{ borderTop: '1px solid #f1f5f9', paddingTop: '20px' }}>
              <h5 style={{ marginTop: 0, marginBottom: '10px', fontSize: '13px', fontWeight: '700', color: '#64748b' }}>
                📚 Verified Ground Truth Fragments Used (Qdrant Cloud Match)
              </h5>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {results.sources.map((source, idx) => (
                  <div key={idx} style={{ backgroundColor: '#f8fafc', padding: '14px', borderRadius: '8px', border: '1px solid #e2e8f0', fontSize: '13px', color: '#334155', lineHeight: '1.5' }}>
                    <span style={{ fontWeight: '700', color: '#94a3b8', marginRight: '6px' }}>[{idx + 1}]</span>
                    {source}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

      </div>
    </div>
  );
}

export default App;