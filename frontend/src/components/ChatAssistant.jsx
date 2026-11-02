import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, AlertCircle, Loader2, Info, Sparkles } from 'lucide-react';
import { sendChatMessage } from '../api';

const QUICK_PROMPTS = [
  { label: 'मराठी', text: 'माझ्या सोयाबीन पिकावर पिवळे डाग पडले आहेत, काय उपाय करावेत?' },
  { label: 'English', text: 'Should I spray pesticides given the 3-day rain forecast?' },
  { label: 'हिन्दी', text: 'कपास की फसल में फूल और बोंड झड़ने से रोकने के क्या उपाय हैं?' },
  { label: 'मराठी', text: 'पावसाची शक्यता असताना खत व्यवस्थापन कसे करावे?' },
];

/**
 * Reusable Chat Assistant Component.
 * Supports Marathi, Hindi, and English with offline rule-based fallback handling.
 */
export default function ChatAssistant({ location, style = {} }) {
  const [messages, setMessages] = useState([
    {
      sender: 'ai',
      text: (
        "नमस्कार शेतकरी बंधूंनो! मी कृषिरक्षक AI आहे.\n" +
        "तुम्ही सोयाबीन, कापूस पिकांचे व्यवस्थापन, स्थानिक हवामान अंदाज, आणि कीड-रोग प्रतिबंधाविषयी प्रश्न विचारू शकता.\n\n" +
        "Ask questions in Marathi, Hindi, or English. I provide cautious guidance based on local Open-Meteo forecasts and verified ICAR advisories."
      ),
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    },
  ]);

  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const handleSend = async (textToSend = input) => {
    const cleanText = textToSend.trim();
    if (!cleanText || loading) return;

    const userMsg = {
      sender: 'user',
      text: cleanText,
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setLoading(true);
    setError('');

    try {
      const response = await sendChatMessage(cleanText, location);
      const aiMsg = {
        sender: 'ai',
        text: response.response,
        weatherIncluded: response.weather_included,
        fallbackUsed: response.fallback_used,
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, aiMsg]);
    } catch (err) {
      setError(err.message || 'Unable to connect to assistant service.');
      const fallbackMsg = {
        sender: 'ai',
        text: (
          "⚠️ माफ करा, AI सेवेशी संपर्क होऊ शकला नाही (API service limit or offline). " +
          "स्थानिक हवामान आणि पीक सल्ल्यासाठी तुम्ही डॅशबोर्डवरील समर्पित साधनांचा वापर करू शकता."
        ),
        fallbackUsed: true,
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, fallbackMsg]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="chat-assistant-component" style={{ display: 'flex', flexDirection: 'column', height: '100%', ...style }}>
      {/* Quick Prompts Bar */}
      <div style={{ marginBottom: '0.75rem', display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
        {QUICK_PROMPTS.map((p, idx) => (
          <button
            key={idx}
            type="button"
            onClick={() => handleSend(p.text)}
            className="btn btn-secondary"
            disabled={loading}
            style={{ fontSize: '0.75rem', padding: '0.3rem 0.6rem', borderRadius: 'var(--radius-full)' }}
          >
            <span style={{ fontWeight: 700, color: 'var(--primary-dark)', marginRight: '0.25rem' }}>{p.label}:</span>
            {p.text.length > 35 ? `${p.text.slice(0, 35)}...` : p.text}
          </button>
        ))}
      </div>

      {/* Messages Thread Container */}
      <div
        tabIndex={0}
        aria-label="Conversation thread"
        style={{
          flex: 1,
          minHeight: '360px',
          maxHeight: '520px',
          overflowY: 'auto',
          padding: '1rem',
          backgroundColor: '#f9fbf9',
          borderRadius: 'var(--radius-md)',
          border: '1px solid var(--border-color)',
          display: 'flex',
          flexDirection: 'column',
          gap: '1rem',
          marginBottom: '1rem',
        }}
      >
        {messages.map((msg, index) => {
          const isAi = msg.sender === 'ai';
          return (
            <div
              key={index}
              style={{
                display: 'flex',
                gap: '0.65rem',
                alignItems: 'flex-start',
                alignSelf: isAi ? 'flex-start' : 'flex-end',
                maxWidth: '85%',
              }}
            >
              {isAi && (
                <div
                  style={{
                    width: '32px',
                    height: '32px',
                    borderRadius: '50%',
                    backgroundColor: 'var(--bg-leaf)',
                    color: 'var(--primary-dark)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    flexShrink: 0,
                    marginTop: '2px',
                  }}
                >
                  <Bot size={18} />
                </div>
              )}

              <div
                style={{
                  padding: '0.75rem 1rem',
                  borderRadius: 'var(--radius-md)',
                  backgroundColor: isAi ? '#ffffff' : 'var(--primary-color)',
                  color: isAi ? 'var(--text-primary)' : '#ffffff',
                  border: isAi ? '1px solid var(--border-color)' : 'none',
                  boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
                  lineHeight: 1.5,
                  fontSize: '0.925rem',
                  whiteSpace: 'pre-wrap',
                  wordBreak: 'break-word',
                }}
              >
                <div>{msg.text}</div>

                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    gap: '0.5rem',
                    marginTop: '0.35rem',
                    fontSize: '0.7rem',
                    color: isAi ? 'var(--text-muted)' : 'rgba(255,255,255,0.8)',
                  }}
                >
                  <span>{msg.time}</span>
                  {msg.fallbackUsed && (
                    <span style={{ color: '#e65100', fontWeight: 600 }}>• Offline Rule-Based Mode</span>
                  )}
                  {msg.weatherIncluded && (
                    <span style={{ color: isAi ? 'var(--primary-color)' : '#ffffff' }}>• Weather Context Active</span>
                  )}
                </div>
              </div>

              {!isAi && (
                <div
                  style={{
                    width: '32px',
                    height: '32px',
                    borderRadius: '50%',
                    backgroundColor: 'var(--primary-dark)',
                    color: '#ffffff',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    flexShrink: 0,
                    marginTop: '2px',
                  }}
                >
                  <User size={18} />
                </div>
              )}
            </div>
          );
        })}

        {loading && (
          <div style={{ display: 'flex', gap: '0.65rem', alignItems: 'center', alignSelf: 'flex-start' }}>
            <div
              style={{
                width: '32px',
                height: '32px',
                borderRadius: '50%',
                backgroundColor: 'var(--bg-leaf)',
                color: 'var(--primary-dark)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <Bot size={18} />
            </div>
            <div
              style={{
                padding: '0.65rem 1rem',
                borderRadius: 'var(--radius-md)',
                backgroundColor: '#ffffff',
                border: '1px solid var(--border-color)',
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                fontSize: '0.85rem',
                color: 'var(--text-secondary)',
              }}
            >
              <Loader2 size={16} className="spin-animation" style={{ color: 'var(--primary-color)' }} />
              <span>Analyzing agricultural advice & forecast...</span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Form */}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          handleSend();
        }}
        style={{ display: 'flex', gap: '0.5rem' }}
      >
        <input
          type="text"
          className="form-control"
          placeholder="Ask a farming question (e.g. कापसावर बोंडअळी दिसल्यास काय करावे?)..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={loading}
          aria-label="Ask farming question"
          style={{ height: '48px', fontSize: '0.95rem' }}
        />
        <button
          type="submit"
          className="btn btn-primary"
          disabled={loading || !input.trim()}
          style={{ width: '52px', height: '48px', padding: 0, display: 'flex', alignItems: 'center', justifyContent: 'center' }}
          aria-label="Send message"
        >
          <Send size={18} />
        </button>
      </form>
    </div>
  );
}
