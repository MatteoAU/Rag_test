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
        <div className="glass-panel animate-fade-in" style={{
            padding: '3rem',
            maxWidth: '420px',
            width: '100%',
            margin: 'auto'
        }}>
            {/* Logo/Brand */}
            <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
                <div style={{
                    width: '64px',
                    height: '64px',
                    background: 'var(--gradient-red)',
                    borderRadius: '16px',
                    display: 'inline-flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    marginBottom: '1.5rem',
                    boxShadow: 'var(--shadow-red)'
                }}>
                    <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2">
                        <path d="M12 2L2 7l10 5 10-5-10-5z" />
                        <path d="M2 17l10 5 10-5" />
                        <path d="M2 12l10 5 10-5" />
                    </svg>
                </div>
                <h2 style={{ marginBottom: '0.5rem' }}>Welcome Back</h2>
                <p style={{ color: 'var(--text-muted)', fontSize: '0.95rem', margin: 0 }}>
                    Sign in to access your RAG System
                </p>
            </div>

            <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                <div>
                    <label style={{
                        display: 'block',
                        marginBottom: '0.5rem',
                        fontSize: '0.875rem',
                        color: 'var(--text-secondary)',
                        fontWeight: '500'
                    }}>
                        Username
                    </label>
                    <input
                        type="text"
                        className="glass-input"
                        placeholder="Enter your username"
                        value={username}
                        onChange={(e) => setUsername(e.target.value)}
                        required
                        autoComplete="username"
                    />
                </div>

                <div>
                    <label style={{
                        display: 'block',
                        marginBottom: '0.5rem',
                        fontSize: '0.875rem',
                        color: 'var(--text-secondary)',
                        fontWeight: '500'
                    }}>
                        Password
                    </label>
                    <input
                        type="password"
                        className="glass-input"
                        placeholder="Enter your password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        required
                        autoComplete="current-password"
                    />
                </div>

                {error && (
                    <div className="status-error" style={{
                        padding: '0.75rem 1rem',
                        borderRadius: '8px',
                        fontSize: '0.875rem',
                        textAlign: 'center'
                    }}>
                        {error}
                    </div>
                )}

                <button
                    type="submit"
                    className="glass-button"
                    disabled={loading}
                    style={{
                        marginTop: '0.5rem',
                        padding: '0.875rem',
                        fontSize: '1rem',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        gap: '0.5rem'
                    }}
                >
                    {loading ? (
                        <>
                            <span className="spinner"></span>
                            Signing in...
                        </>
                    ) : 'Sign In'}
                </button>
            </form>

            <div style={{
                marginTop: '2rem',
                paddingTop: '1.5rem',
                borderTop: '1px solid var(--border-color)',
                textAlign: 'center',
                fontSize: '0.875rem',
                color: 'var(--text-muted)'
            }}>
                RAG Vector Database System
            </div>
        </div>
    );
}
