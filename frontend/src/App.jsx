import React, { useState, useEffect } from 'react';

function App() {
  const [text, setText] = useState('');
  const [query, setQuery] = useState('');
  const [results, setResults] = useState({ answer: '', sources: [] });
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [sessionId, setSessionId] = useState('');
  const [selectedFile, setSelectedFile] = useState(null);

  // Generate an atomic session identity string safe across all browser networks
  useEffect(() => {
    const generateSafeId = () => {
      return Math.random().toString(36).substring(2, 15) + 
             Math.random().toString(36).substring(2, 15);
    };
    setSessionId(generateSafeId());
  }, []);

  const API_URL = window.location.hostname === 'localhost' 
    ? 'http://localhost:8000' 
    : `http://${window.location.hostname}:8000`;

  // Action 1: Upload Raw Text Snippets
  const handleTextUpload = async () => {
    if (!text.trim()) return;
    setUploading(true);
    setMessage('Vectorizing context parameters...');
    try {
      const res = await fetch(`${API_URL}/upload`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text, session_id: sessionId })
      });
      const data = await res.json();
      if (res.ok) {
        setMessage(data.message || '✨ Context successfully isolated to your current session!');
        setText('');
      } else {
        setMessage(`❌ Error: ${data.detail || 'Failed to parse inputs.'}`);
      }
    } catch (err) {
      setMessage('❌ Error communicating with the server pipeline.');
    } finally {
      setUploading(false);
    }
  };

  // Action 2: Upload Raw Binary PDF Files
  const handleFileUpload = async () => {
    if (!selectedFile) return;
    setUploading(true);
    setMessage('Parsing PDF pages & extraction layers...');
    
    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('session_id', sessionId);

    try {
      const res = await fetch(`${API_URL}/upload-file`, {
        method: 'POST',
        body: formData
      });
      const data = await res.json();
      if (res.ok) {
        setMessage(data.message || `✨ Successfully vectorized and indexed file metadata context!`);
        setSelectedFile(null);
        document.getElementById("filePicker").value = "";
      } else {
        setMessage(`❌ Error: ${data.detail || 'Failed to extract content.'}`);
      }
    } catch (err) {
      setMessage('❌ Connection to document server failed.');
    } finally {
      setUploading(false);
    }
  };

  // Action 3: Bulk Delete Session Vectors
  const handleClearSession = async () => {
    if (!window.confirm("Are you sure you want to completely clear all data points from this session canvas?")) return;
    setLoading(true);
    setMessage('Wiping session vectors...');
    try {
      const res = await fetch(`${API_URL}/clear-session`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: '', session_id: sessionId })
      });
      if (res.ok) {
        setMessage('🧹 All session data deleted! Canvas is fresh and empty.');
        setResults({ answer: '', sources: [] });
        setText('');
        setSelectedFile(null);
      } else {
        alert('Failed to execute bulk deletion on cluster.');
      }
    } catch (err) {
      alert('Network error trying to clear session.');
    } finally {
      setLoading(false);
    }
  };

  // Action 4: RAG Synthesis Pipeline Execution
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
        alert(`Core Failure Response: ${data.detail}`);
      }
    } catch (err) {
      alert('Error extracting target query matrix.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ backgroundColor: '#f8fafc', minHeight: '100vh', padding: '40px 20px', fontFamily: '"Inter", system-ui, sans-serif', color: '#1e293b' }}>
      <div style={{ maxWidth: '750px', margin: '0 auto' }}>
        
        {/* Header Block */}
        <header style={{ textAlign: 'center', marginBottom: '40px' }}>
          <h1 style={{ fontSize: '32px', fontWeight: '800', color: '#0f172a', margin: '0 0 8px 0', letterSpacing: '-0.025em' }}>
            ⚡ Light-RAG Sandbox
          </h1>
          <p style={{ fontSize: '15px', color: '#64748b', margin: '0 0 16px 0', fontWeight: '500' }}>
            Gemini 2.5 Flash + Qdrant Cloud Cluster Engine
          </p>
          <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
            <div style={{ padding: '6px 12px', backgroundColor: '#e2e8f0', borderRadius: '20px', fontSize: '12px', fontWeight: '600', color: '#475569' }}>
              Active Sandbox Token: <span style={{ fontFamily: 'monospace', color: '#2563eb' }}>{sessionId ? sessionId.substring(0, 8) + '...' : 'initializing'}</span>
            </div>
            <button 
              onClick={handleClearSession}
              style={{ padding: '6px 14px', backgroundColor: '#fee2e2', color: '#ef4444', border: '1px solid #fca5a5', borderRadius: '20px', fontSize: '12px', fontWeight: '600', cursor: 'pointer', transition: 'all 0.2s' }}
              onMouseEnter={(e) => e.target.style.backgroundColor = '#fecaca'}
              onMouseLeave={(e) => e.target.style.backgroundColor = '#fee2e2'}
            >
              🗑️ Clear Canvas Data
            </button>
          </div>
        </header>

        {/* Card 1: Dynamic Data Ingestion Matrix */}
        <div style={{ backgroundColor: '#ffffff', border: '1px solid #e2e8f0', padding: '28px', borderRadius: '16px', boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.05)', marginBottom: '28px' }}>
          <h3 style={{ marginTop: 0, fontSize: '18px', fontWeight: '700', color: '#334155', marginBottom: '6px' }}>
            1. Ingest Factual Context
          </h3>
          <p style={{ fontSize: '13px', color: '#64748b', marginTop: 0, marginBottom: '16px' }}>
            Every browser tab fresh-start builds an isolated environment. Choose to input raw text snippets OR upload an entire document.
          </p>
          
          <textarea 
            style={{ width: '100%', height: '90px', padding: '14px', boxSizing: 'border-box', borderRadius: '8px', border: '1px solid #cbd5e1', fontSize: '14px', marginBottom: '12px', resize: 'vertical', fontFamily: 'inherit', outline: 'none' }} 
            value={text} 
            onChange={(e) => setText(e.target.value)} 
            placeholder="Paste raw text, knowledge updates, logs..." 
            disabled={!!selectedFile}
          />
          
          <div style={{ textTransform: 'uppercase', fontSize: '11px', color: '#94a3b8', fontWeight: '700', letterSpacing: '0.05em', textAlign: 'center', marginBottom: '12px' }}>— OR —</div>

          <div style={{ padding: '16px', border: '2px dashed #cbd5e1', borderRadius: '8px', backgroundColor: '#f8fafc', textAlign: 'center', marginBottom: '14px' }}>
            <input 
              id="filePicker"
              type="file" 
              accept=".pdf" 
              onChange={(e) => setSelectedFile(e.target.files[0])}
              style={{ fontSize: '14px', color: '#475569' }}
              disabled={!!text.trim()}
            />
          </div>

          {selectedFile ? (
            <button 
              style={{ padding: '12px 24px', backgroundColor: '#7c3aed', color: '#ffffff', border: 'none', borderRadius: '8px', cursor: 'pointer', fontWeight: '600', fontSize: '14px', boxShadow: '0 2px 4px rgba(124, 58, 237, 0.2)' }} 
              onClick={handleFileUpload}
              disabled={uploading}
            >
              {uploading ? 'Parsing PDF Structural Layout...' : 'Upload & Process PDF File'}
            </button>
          ) : (
            <button 
              style={{ padding: '12px 24px', backgroundColor: '#2563eb', color: '#ffffff', border: 'none', borderRadius: '8px', cursor: text.trim() ? 'pointer' : 'not-allowed', fontWeight: '600', fontSize: '14px', opacity: text.trim() && !uploading ? 1 : 0.6, boxShadow: '0 2px 4px rgba(37, 99, 235, 0.2)' }} 
              onClick={handleTextUpload}
              disabled={!text.trim() || uploading}
            >
              {uploading ? 'Vectorizing...' : 'Upload Text Snippet'}
            </button>
          )}
          
          {message && (
            <div style={{ display: 'flex', alignItems: 'center', backgroundColor: message.includes('❌') ? '#fef2f2' : '#f0f9ff', padding: '12px 16px', borderRadius: '8px', marginTop: '16px', borderLeft: `4px solid ${message.includes('❌') ? '#ef4444' : '#0284c7'}` }}>
              <span style={{ fontSize: '14px', fontWeight: '500', color: message.includes('❌') ? '#991b1b' : '#0369a1' }}>{message}</span>
            </div>
          )}
        </div>

        {/* Card 2: Retrieval Engine UI */}
        <div style={{ backgroundColor: '#ffffff', border: '1px solid #e2e8f0', padding: '28px', borderRadius: '16px', boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.05)' }}>
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
              style={{ padding: '0 28px', backgroundColor: '#10b981', color: '#ffffff', border: 'none', borderRadius: '8px', cursor: query.trim() ? 'pointer' : 'not-allowed', fontWeight: '600', fontSize: '14px', opacity: query.trim() && !loading ? 1 : 0.6, boxShadow: '0 2px 4px rgba(16, 185, 129, 0.2)' }} 
              onClick={handleSearch}
              disabled={!query.trim() || loading}
            >
              {loading ? 'Analyzing...' : 'Query'}
            </button>
          </div>

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

          {results.sources.length > 0 && (
            <div style={{ borderTop: '1px solid #f1f5f9', paddingTop: '20px' }}>
              <h5 style={{ marginTop: 0, marginBottom: '10px', fontSize: '13px', fontWeight: '700', color: '#64748b' }}>
                📚 Verified Ground Truth Fragments Used (Qdrant Cloud Match)
              </h5>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {results.sources.map((source, idx) => (
                  <div key={idx} style={{ backgroundColor: '#f8fafc', padding: '14px', borderRadius: '8px', border: '1px solid #e2e8f0', fontSize: '13px', color: '#334155', lineHeight: '1.5' }}>
                    <span style={{ fontWeight: '700', color: '#94a3b8', marginRight: '6px' }}>[{idx + 1}]</span>
                    {source.substring(0, 400)}{source.length > 400 ? '...' : ''}
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