import { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import { api } from '../services/api';

export function ChatInterface({ token, dbHash }) {
    const [query, setQuery] = useState('');
    const [messages, setMessages] = useState([]);
    const [loading, setLoading] = useState(false);
    const scrollRef = useRef(null);

    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [messages]);

    const handleQuery = async (e) => {
        e.preventDefault();
        if (!query.trim()) return;

        const userMsg = { role: 'user', content: query };
        setMessages(prev => [...prev, userMsg]);
        setQuery('');
        setLoading(true);

        try {
            const res = await api.query(token, dbHash, userMsg.content);
            const assistantMsg = {
                role: 'assistant',
                content: res.answer,
                sources: res.sources
            };
            setMessages(prev => [...prev, assistantMsg]);
        } catch (err) {
            setMessages(prev => [...prev, { role: 'assistant', content: '**Error:** Failed to get response.' }]);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div style={{ display: 'flex', flexDirection: 'column', height: '100%', gap: '1rem' }}>
            {/* Chat Messages Area */}
            <div
                ref={scrollRef}
                style={{
                    flex: 1,
                    overflowY: 'auto',
                    padding: '1rem',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '1rem',
                    background: 'var(--bg-tertiary)',
                    borderRadius: '12px',
                    border: '1px solid var(--border-color)'
                }}
            >
                {messages.length === 0 && (
                    <div style={{
                        textAlign: 'center',
                        padding: '3rem 1rem',
                        color: 'var(--text-muted)',
                        display: 'flex',
                        flexDirection: 'column',
                        alignItems: 'center',
                        gap: '1rem'
                    }}>
                        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" opacity="0.4">
                            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
                        </svg>
                        <span>Ask a question about your documents...</span>
                    </div>
                )}

                {messages.map((msg, idx) => (
                    <div
                        key={idx}
                        className="animate-fade-in"
                        style={{
                            alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start',
                            maxWidth: '85%',
                            background: msg.role === 'user'
                                ? 'var(--gradient-red)'
                                : 'var(--bg-secondary)',
                            padding: '1rem 1.25rem',
                            borderRadius: '16px',
                            borderTopRightRadius: msg.role === 'user' ? '4px' : '16px',
                            borderTopLeftRadius: msg.role === 'assistant' ? '4px' : '16px',
                            border: msg.role === 'assistant' ? '1px solid var(--border-color)' : 'none',
                            boxShadow: msg.role === 'user' ? 'var(--shadow-red)' : 'var(--shadow-sm)'
                        }}
                    >
                        <div style={{
                            fontSize: '0.7rem',
                            color: msg.role === 'user' ? 'rgba(255,255,255,0.7)' : 'var(--text-muted)',
                            marginBottom: '0.5rem',
                            fontWeight: '600',
                            textTransform: 'uppercase',
                            letterSpacing: '0.5px'
                        }}>
                            {msg.role === 'user' ? 'You' : 'AI Assistant'}
                        </div>
                        <div className="markdown-content" style={{ lineHeight: '1.6' }}>
                            {msg.role === 'assistant' ? (
                                <ReactMarkdown>{msg.content}</ReactMarkdown>
                            ) : (
                                msg.content
                            )}
                        </div>
                        {msg.sources && msg.sources.length > 0 && (
                            <div style={{
                                marginTop: '1rem',
                                borderTop: '1px solid var(--border-color)',
                                paddingTop: '0.75rem',
                                fontSize: '0.8rem'
                            }}>
                                <div style={{
                                    color: 'var(--text-muted)',
                                    fontWeight: '600',
                                    fontSize: '0.7rem',
                                    textTransform: 'uppercase',
                                    letterSpacing: '0.5px',
                                    marginBottom: '0.5rem'
                                }}>
                                    Sources
                                </div>
                                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                                    {msg.sources.map((s, i) => (
                                        <span
                                            key={i}
                                            className="badge"
                                            style={{ fontSize: '0.75rem' }}
                                        >
                                            {s.filename} ({(s.score * 100).toFixed(0)}%)
                                        </span>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>
                ))}
                {loading && (
                    <div className="animate-fade-in" style={{
                        alignSelf: 'flex-start',
                        padding: '1rem 1.25rem',
                        background: 'var(--bg-secondary)',
                        borderRadius: '16px',
                        borderTopLeftRadius: '4px',
                        border: '1px solid var(--border-color)',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.75rem',
                        color: 'var(--text-muted)'
                    }}>
                        <span className="spinner"></span>
                        Thinking...
                    </div>
                )}
            </div>

            {/* Input Area */}
            <form onSubmit={handleQuery} style={{ display: 'flex', gap: '0.75rem' }}>
                <input
                    type="text"
                    className="glass-input"
                    placeholder="Type your question..."
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    disabled={loading}
                    style={{ flex: 1 }}
                />
                <button
                    type="submit"
                    className="glass-button"
                    disabled={loading || !query.trim()}
                    style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.5rem',
                        padding: '0.75rem 1.25rem'
                    }}
                >
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <line x1="22" y1="2" x2="11" y2="13" />
                        <polygon points="22 2 15 22 11 13 2 9 22 2" />
                    </svg>
                    Send
                </button>
            </form>
        </div>
    );
}
