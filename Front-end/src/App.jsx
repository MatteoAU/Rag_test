import { useState } from 'react'
import { Login } from './components/Login'
import { Dashboard } from './components/Dashboard'
import './App.css'

function App() {
  const [token, setToken] = useState(localStorage.getItem('access_token'))

  const handleLogin = (accessToken) => {
    localStorage.setItem('access_token', accessToken);
    setToken(accessToken);
  }

  return (
    <div className="app-container">
      {!token ? (
        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
          <Login onLogin={handleLogin} />
        </div>
      ) : (
        <Dashboard token={token} />
      )}
    </div>
  )
}

export default App
