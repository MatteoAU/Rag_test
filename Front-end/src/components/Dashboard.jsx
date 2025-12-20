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
        if (!confirm('Are you sure you want to delete this DB?')) return;
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
            await loadDbs(); // refresh counts
            setFile(null);
        } catch (err) {
            console.error(err);
            if (err.status === 401 && onLogout) {
                onLogout();
            } else {
                setMessage({ type: 'error', text: 'Upload failed' });
            }
        } finally {
            setUploading(false);
        }
    };

    return (
        <div style={{ display: 'flex', width: '100%', height: '100%' }}>
            {/* Sidebar - DB List */}
            <div className="glass-panel" style={{
                width: '300px',
                margin: '10px',
                display: 'flex',
                flexDirection: 'column',
                borderRadius: '16px 0 0 16px',
                borderRight: '1px solid var(--glass-border)'
            }}>
                <div style={{ padding: '1.5rem', borderBottom: '1px solid var(--glass-border)' }}>
                    <h2 style={{ margin: 0, fontSize: '1.2rem' }}>Vector DBs</h2>
                    <button
                        className="glass-button"
                        style={{ width: '100%', marginTop: '1rem', fontSize: '0.9rem' }}
                        onClick={handleCreateDB}
                        disabled={creating}
                    >
                        {creating ? 'Creating...' : '+ New Database'}
                    </button>
                </div>

                <div style={{ overflowY: 'auto', flex: 1, padding: '1rem' }}>
                    {loading ? <p style={{ opacity: 0.5, textAlign: 'center' }}>Loading...</p> : (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                            {dbs.map((db) => (
                                <div
                                    key={db.db_hash}
                                    onClick={() => setSelectedDb(db.db_hash)}
                                    style={{
                                        padding: '1rem',
                                        borderRadius: '8px',
                                        background: selectedDb === db.db_hash ? 'var(--glass-highlight)' : 'transparent',
                                        cursor: 'pointer',
                                        border: '1px solid transparent',
                                        transition: 'all 0.2s'
                                    }}
                                    className="db-item"
                                >
                                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                        <span style={{ fontWeight: 500, fontSize: '0.9rem' }}>{db.db_hash.substring(0, 8)}...</span>
                                        <button
                                            onClick={(e) => { e.stopPropagation(); handleDeleteDB(db.db_hash); }}
                                            style={{ background: 'none', border: 'none', color: '#ff6b6b', cursor: 'pointer', padding: '5px' }}
                                        >
                                            ✕
                                        </button>
                                    </div>
                                    <div style={{ fontSize: '0.8rem', opacity: 0.7, marginTop: '5px' }}>
                                        {db.vectors_count} vectors
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </div>

            {/* Main Content - Upload & Actions (Later Chat) */}
            <div style={{ flex: 1, padding: '2rem' }}>
                {!selectedDb ? (
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', opacity: 0.5 }}>
                        <p>Select a Database to manage</p>
                    </div>
                ) : (
                    <div className="glass-panel" style={{ padding: '2rem', height: '100%', boxSizing: 'border-box', display: 'flex', flexDirection: 'column' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                            <h2>Manage Database: <span style={{ fontFamily: 'monospace', opacity: 0.8 }}>{selectedDb}</span></h2>
                        </div>

                        {/* Upload Section */}
                        <div style={{ padding: '1.5rem', background: 'rgba(0,0,0,0.2)', borderRadius: '12px', marginBottom: '2rem' }}>
                            <h3 style={{ marginTop: 0 }}>Upload Documents</h3>
                            <form onSubmit={handleUpload} style={{ display: 'flex', gap: '1rem', alignItems: 'center', flexWrap: 'wrap' }}>
                                <input
                                    type="file"
                                    onChange={(e) => setFile(e.target.files[0])}
                                    className="glass-input"
                                    style={{ flex: 1, minWidth: '200px' }}
                                />
                                <button type="submit" className="glass-button" disabled={uploading || !file}>
                                    {uploading ? 'Uploading...' : 'Upload'}
                                </button>
                            </form>
                            {message && (
                                <div style={{
                                    marginTop: '1rem',
                                    padding: '1rem',
                                    borderRadius: '8px',
                                    background: message.type === 'success' ? 'rgba(46, 204, 113, 0.2)' : 'rgba(231, 76, 60, 0.2)',
                                    border: message.type === 'success' ? '1px solid rgba(46, 204, 113, 0.4)' : '1px solid rgba(231, 76, 60, 0.4)'
                                }}>
                                    {message.text}
                                </div>
                            )}
                        </div>

                        {/* Chat Section */}
                        <div style={{ flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
                            <h3 style={{ marginTop: 0 }}>Chat</h3>
                            <div style={{ flex: 1, overflow: 'hidden' }}>
                                <ChatInterface token={token} dbHash={selectedDb} />
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
