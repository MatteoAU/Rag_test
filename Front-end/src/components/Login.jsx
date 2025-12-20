import { useState } from 'react';
import { api } from '../services/api';

export function Login({ onLogin }) {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState(null);
    const [loading, setLoading] = useState(false);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError(null);
        try {
            const data = await api.login(username, password);
            onLogin(data.access_token);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="glass-panel" style={{ padding: '3rem', maxWidth: '400px', margin: 'auto', width: '100%' }}>
            <h2 style={{ marginTop: 0, textAlign: 'center' }}>Welcome Back</h2>
            <p style={{ textAlign: 'center', opacity: 0.7, marginBottom: '2rem' }}>Sign in to access your RAG Dashboard</p>

            <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                <div>
                    <input
                        type="text"
                        className="glass-input"
                        placeholder="Username"
                        value={username}
                        onChange={(e) => setUsername(e.target.value)}
                        required
                    />
                </div>
                <div>
                    <input
                        type="password"
                        className="glass-input"
                        placeholder="Password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        required
                    />
                </div>

                {error && <div style={{ color: '#ff6b6b', fontSize: '0.9em', textAlign: 'center' }}>{error}</div>}

                <button type="submit" className="glass-button" disabled={loading} style={{ marginTop: '1rem' }}>
                    {loading ? 'Signing in...' : 'Sign In'}
                </button>
            </form>
        </div>
    );
}
