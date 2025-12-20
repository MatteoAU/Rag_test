import { useState, useEffect } from 'react'
import { Login } from './components/Login'
import { Dashboard } from './components/Dashboard'
import { api } from './services/api'
import './App.css'

function App() {
  const [token, setToken] = useState(() => localStorage.getItem('access_token'))
  const [loading, setLoading] = useState(() => !!localStorage.getItem('access_token'))
  const [error, setError] = useState(null)

  useEffect(() => {
    if (!token) {
      setLoading(false);
      return;
    }

    const verify = async () => {
      try {
        await api.getVectors(token);
        setLoading(false);
      } catch (e) {
        console.error("Token verification failed:", e);
        // Only logout on 401, otherwise might be network error
        if (e.status === 401) {
          localStorage.removeItem('access_token');
          setToken(null);
        }
        // If network error, we still allow Dashboard to try rendering (it handles its own errors)
        setLoading(false);
      }
    };
    verify();
  }, [token]);

  const handleLogin = (accessToken) => {
    localStorage.setItem('access_token', accessToken);
    setToken(accessToken);
    setLoading(false);
  }

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    setToken(null);
    setLoading(false);
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
