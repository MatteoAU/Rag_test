import { useState, useEffect } from 'react'
import { Login } from './components/Login'
import { Dashboard } from './components/Dashboard'
import { api } from './services/api'
import './App.css'

function App() {
  // Token stored only in memory - requires login on every app open
  const [token, setToken] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  // Clear any old tokens from localStorage on mount
  useEffect(() => {
    localStorage.removeItem('access_token');
  }, []);

  const handleLogin = (accessToken) => {
    // Token is only stored in memory, not persisted
    setToken(accessToken);
  }

  const handleLogout = () => {
    setToken(null);
  }

  if (error) {
    return <div style={{ color: 'red', padding: 20 }}>Fatal Error: {error.message}</div>
  }

  if (loading) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        height: '100vh',
        color: 'white'
      }}>
        Loading RAG System...
      </div>
    );
  }

  return (
    <div className="app-container">
      {!token ? (
        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
          <Login onLogin={handleLogin} />
        </div>
      ) : (
        <Dashboard token={token} onLogout={handleLogout} />
      )}
    </div>
  )
}

export default App
