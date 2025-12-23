import { useState, useEffect } from 'react';
import { ChatInterface } from './ChatInterface';
import { api } from '../services/api';

export function Dashboard({ token, onLogout }) {
    const [dbs, setDbs] = useState([]);
    const [loading, setLoading] = useState(true);
    const [creating, setCreating] = useState(false);
    const [selectedDb, setSelectedDb] = useState(null);
    const [uploading, setUploading] = useState(false);
    const [file, setFile] = useState(null);
    const [message, setMessage] = useState(null);
    const [warmupStatus, setWarmupStatus] = useState(null);
    const [warmingUp, setWarmingUp] = useState(false);

    useEffect(() => {
        loadDbs();
    }, [token]);

    const loadDbs = async () => {
        try {
            const data = await api.getVectors(token);
            setDbs(data.databases || []);
        } catch (err) {
            console.error(err);
            if (err.status === 401 && onLogout) {
                onLogout();
            }
        } finally {
            setLoading(false);
        }
    };

    const handleWarmup = async () => {
        setWarmingUp(true);
        setWarmupStatus(null);
        try {
            const result = await api.warmup(token);
            setWarmupStatus(result);
        } catch (err) {
            console.error(err);
            if (err.status === 401 && onLogout) {
                onLogout();
            } else {
                setWarmupStatus({ status: 'error', message: err.message });
            }
        } finally {
            setWarmingUp(false);
        }
    };

    const handleCreateDB = async () => {
        setCreating(true);
        try {
            await api.createDB(token);
            await loadDbs();
        } catch (err) {
            console.error(err);
            if (err.status === 401 && onLogout) {
                onLogout();
            } else {
                alert('Failed to create DB');
            }
        } finally {
            setCreating(false);
        }
    };

    const handleDeleteDB = async (dbHash) => {
        if (!confirm('Are you sure you want to delete this database?')) return;
        try {
            await api.deleteDB(token, dbHash);
            if (selectedDb === dbHash) setSelectedDb(null);
            await loadDbs();
        } catch (err) {
            console.error(err);
            if (err.status === 401 && onLogout) {
                onLogout();
            } else {
                alert('Failed to delete DB');
            }
        }
    };

    const handleUpload = async (e) => {
        e.preventDefault();
        if (!file || !selectedDb) return;

        setUploading(true);
        setMessage(null);
        try {
            const res = await api.uploadFile(token, selectedDb, file);
            setMessage({ type: 'success', text: `Uploaded ${res.filename} (${res.vectors_stored} vectors)` });
            await loadDbs();
            setFile(null);
        } catch (err) {
            console.error(err);
            if (err.status === 401 && onLogout) {
                onLogout();
            } else {
                setMessage({ type: 'error', text: err.message || 'Upload failed' });
            }
        } finally {
            setUploading(false);
        }
    };

    return (
        <div style={{ display: 'flex', minHeight: '100vh', background: 'var(--bg-primary)' }}>
            {/* Sidebar */}
            <aside style={{
                width: '320px',
                background: 'var(--bg-secondary)',
                borderRight: '1px solid var(--border-color)',
                display: 'flex',
                flexDirection: 'column'
            }}>
                {/* Header */}
                <div style={{
                    padding: '1.5rem',
                    borderBottom: '1px solid var(--border-color)',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.75rem'
                }}>
                    <div style={{
                        width: '40px',
                        height: '40px',
                        background: 'var(--gradient-red)',
                        borderRadius: '10px',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        boxShadow: 'var(--shadow-red)'
                    }}>
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2">
                            <path d="M12 2L2 7l10 5 10-5-10-5z" />
                            <path d="M2 17l10 5 10-5" />
                            <path d="M2 12l10 5 10-5" />
                        </svg>
                    </div>
                    <div>
                        <h3 style={{ margin: 0, fontSize: '1.1rem' }}>RAG System</h3>
                        <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Vector Database</span>
                    </div>
                    <button
                        onClick={onLogout}
                        className="glass-button secondary"
                        style={{ marginLeft: 'auto', padding: '0.5rem 0.75rem', fontSize: '0.8rem' }}
                    >
                        Logout
                    </button>
                </div>

                {/* Warmup Section */}
                <div style={{ padding: '1rem 1.5rem', borderBottom: '1px solid var(--border-color)' }}>
                    <button
                        className="glass-button"
                        style={{ width: '100%', fontSize: '0.875rem', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem' }}
                        onClick={handleWarmup}
                        disabled={warmingUp}
                    >
                        {warmingUp ? (
                            <>
                                <span className="spinner"></span>
                                Warming up LLM...
                            </>
                        ) : (
                            <>
                                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                    <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83" />
                                </svg>
                                Warmup LLM Models
                            </>
                        )}
                    </button>
                    {warmupStatus && (
                        <div style={{ marginTop: '0.75rem', fontSize: '0.8rem' }}>
                            <div className={`status-${warmupStatus.status === 'success' ? 'success' : warmupStatus.status === 'partial' ? 'warning' : 'error'}`}
                                style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', justifyContent: 'center' }}>
                                {warmupStatus.status === 'success' ? '✓ Models Ready' :
                                    warmupStatus.status === 'partial' ? '⚠ Partial Success' : '✕ Warmup Failed'}
                            </div>
                        </div>
                    )}
                </div>

                {/* Database Actions */}
                <div style={{ padding: '1rem 1.5rem', borderBottom: '1px solid var(--border-color)' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
                        <span style={{ fontSize: '0.75rem', fontWeight: '600', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                            Databases
                        </span>
                        <span className="badge">{dbs.length}</span>
                    </div>
                    <button
                        className="glass-button secondary"
                        style={{ width: '100%', fontSize: '0.875rem' }}
                        onClick={handleCreateDB}
                        disabled={creating}
                    >
                        {creating ? 'Creating...' : '+ New Database'}
                    </button>
                </div>

                {/* Database List */}
                <div style={{ flex: 1, overflowY: 'auto', padding: '0.75rem' }}>
                    {loading ? (
                        <div style={{ display: 'flex', justifyContent: 'center', padding: '2rem' }}>
                            <span className="spinner"></span>
                        </div>
                    ) : dbs.length === 0 ? (
                        <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)', fontSize: '0.875rem' }}>
                            No databases yet
                        </div>
                    ) : (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                            {dbs.map((db) => (
                                <div
                                    key={db.db_hash}
                                    onClick={() => setSelectedDb(db.db_hash)}
                                    className="card animate-fade-in"
                                    style={{
                                        padding: '1rem',
                                        cursor: 'pointer',
                                        background: selectedDb === db.db_hash ? 'var(--bg-tertiary)' : 'transparent',
                                        borderColor: selectedDb === db.db_hash ? 'var(--border-red)' : 'var(--border-color)',
                                        borderLeft: selectedDb === db.db_hash ? '3px solid var(--primary-red)' : '3px solid transparent'
                                    }}
                                >
                                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                        <div>
                                            <span style={{
                                                fontFamily: 'monospace',
                                                fontSize: '0.85rem',
                                                fontWeight: '500',
                                                color: 'var(--text-primary)'
                                            }}>
                                                {db.db_hash.substring(0, 12)}...
                                            </span>
                                            <div style={{
                                                fontSize: '0.75rem',
                                                color: 'var(--text-muted)',
                                                marginTop: '0.25rem',
                                                display: 'flex',
                                                alignItems: 'center',
                                                gap: '0.25rem'
                                            }}>
                                                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                                    <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z" />
                                                </svg>
                                                {db.vectors_count} vectors
                                            </div>
                                        </div>
                                        <button
                                            onClick={(e) => { e.stopPropagation(); handleDeleteDB(db.db_hash); }}
                                            className="glass-button danger"
                                            style={{ padding: '0.375rem 0.5rem', fontSize: '0.75rem' }}
                                        >
                                            ✕
                                        </button>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </aside>

            {/* Main Content */}
            <main style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
                {!selectedDb ? (
                    <div style={{
                        flex: 1,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        flexDirection: 'column',
                        gap: '1rem',
                        color: 'var(--text-muted)'
                    }}>
                        <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" opacity="0.3">
                            <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z" />
                            <polyline points="3.27 6.96 12 12.01 20.73 6.96" />
                            <line x1="12" y1="22.08" x2="12" y2="12" />
                        </svg>
                        <p style={{ fontSize: '1rem' }}>Select a database to manage</p>
                    </div>
                ) : (
                    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', padding: '1.5rem', gap: '1.5rem', overflow: 'hidden' }}>
                        {/* Header */}
                        <div className="card" style={{ padding: '1.25rem 1.5rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                            <div>
                                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                                    Active Database
                                </span>
                                <h2 style={{ margin: '0.25rem 0 0 0', fontFamily: 'monospace', fontSize: '1.1rem' }}>
                                    {selectedDb}
                                </h2>
                            </div>
                            <span className="badge badge-red">
                                {dbs.find(d => d.db_hash === selectedDb)?.vectors_count || 0} vectors
                            </span>
                        </div>

                        {/* Upload Section */}
                        <div className="card" style={{ padding: '1.5rem' }}>
                            <h3 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
                                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--primary-red)" strokeWidth="2">
                                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                                    <polyline points="17 8 12 3 7 8" />
                                    <line x1="12" y1="3" x2="12" y2="15" />
                                </svg>
                                Upload Documents
                            </h3>
                            <form onSubmit={handleUpload} style={{ display: 'flex', gap: '1rem', alignItems: 'center', flexWrap: 'wrap' }}>
                                <input
                                    type="file"
                                    onChange={(e) => setFile(e.target.files[0])}
                                    className="glass-input"
                                    style={{ flex: 1, minWidth: '200px' }}
                                />
                                <button type="submit" className="glass-button" disabled={uploading || !file} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                    {uploading ? <><span className="spinner"></span> Uploading...</> : 'Upload'}
                                </button>
                            </form>
                            {message && (
                                <div className={message.type === 'success' ? 'status-success' : 'status-error'}
                                    style={{ marginTop: '1rem', padding: '0.75rem 1rem', borderRadius: '8px' }}>
                                    {message.text}
                                </div>
                            )}
                        </div>

                        {/* Chat Section */}
                        <div className="card" style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden', padding: '1.5rem' }}>
                            <h3 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
                                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--primary-red)" strokeWidth="2">
                                    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
                                </svg>
                                Query Documents
                            </h3>
                            <div style={{ flex: 1, overflow: 'hidden' }}>
                                <ChatInterface token={token} dbHash={selectedDb} />
                            </div>
                        </div>
                    </div>
                )}
            </main>
        </div>
    );
}
