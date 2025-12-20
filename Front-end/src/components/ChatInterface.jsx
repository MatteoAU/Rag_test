import { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import { api } from '../services/api';

export function ChatInterface({ token, dbHash }) {
    const [query, setQuery] = useState('');
    const [messages, setMessages] = useState([]); // { role: 'user' | 'assistant', content: string }
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
            // Ensure we handle the response correctly. res should be JSON QueryResponse
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
                    background: 'rgba(0,0,0,0.1)',
                    borderRadius: '12px'
                }}
            >
                {messages.length === 0 && (
                    <div style={{ opacity: 0.5, textAlign: 'center', marginTop: '2rem' }}>
                        Ask a question about your documents...
                    </div>
                )}

                {messages.map((msg, idx) => (
                    <div
                        key={idx}
                        style={{
                            alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start',
                            maxWidth: '80%',
                            background: msg.role === 'user' ? 'rgba(102, 126, 234, 0.3)' : 'rgba(255, 255, 255, 0.1)',
                            padding: '1rem',
                            borderRadius: '12px',
                            borderTopRightRadius: msg.role === 'user' ? '4px' : '12px',
                            borderTopLeftRadius: msg.role === 'assistant' ? '4px' : '12px',
                        }}
                    >
                        <div style={{ fontSize: '0.8rem', opacity: 0.7, marginBottom: '0.5rem' }}>
                            {msg.role === 'user' ? 'You' : 'AI'}
                        </div>
                        <div className="markdown-content">
                            {msg.role === 'assistant' ? (
                                <ReactMarkdown>{msg.content}</ReactMarkdown>
                            ) : (
                                msg.content
                            )}
                        </div>
                        {msg.sources && msg.sources.length > 0 && (
                            <div style={{ marginTop: '1rem', borderTop: '1px solid rgba(255,255,255,0.1)', paddingTop: '0.5rem', fontSize: '0.85rem' }}>
                                <strong style={{ opacity: 0.8 }}>Sources:</strong>
                                <ul style={{ paddingLeft: '1.2rem', margin: '0.5rem 0 0 0' }}>
                                    {msg.sources.map((s, i) => (
                                        <li key={i} style={{ opacity: 0.7 }}>
                                            {s.filename} (Score: {s.score.toFixed(2)})
                                        </li>
                                    ))}
                                </ul>
                            </div>
                        )}
                    </div>
                ))}
                {loading && (
                    <div style={{ alignSelf: 'flex-start', padding: '1rem', opacity: 0.7 }}>
                        Thinking...
                    </div>
                )}
            </div>

            {/* Input Area */}
            <form onSubmit={handleQuery} style={{ display: 'flex', gap: '1rem' }}>
                <input
                    type="text"
                    className="glass-input"
                    placeholder="Type your question..."
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    disabled={loading}
                />
                <button type="submit" className="glass-button" disabled={loading || !query.trim()}>
                    Send
                </button>
            </form>
        </div>
    );
}
