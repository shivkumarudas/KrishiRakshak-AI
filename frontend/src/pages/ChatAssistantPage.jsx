import React from 'react';
import { MessageSquare, MapPin } from 'lucide-react';
import ChatAssistant from '../components/ChatAssistant';

export default function ChatAssistantPage({ location }) {
  return (
    <div className="container" style={{ maxWidth: '920px' }}>
      {/* Header */}
      <div style={{ marginBottom: '1rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.5rem' }}>
        <div>
          <h2 style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--primary-dark)', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <MessageSquare size={28} /> AI Farming Assistant (कृषिरक्षक मदतनीस)
          </h2>
          <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
            Ask farming questions in Marathi (मराठी), Hindi (हिन्दी), or English.
          </p>
        </div>

        {location && (
          <div
            style={{
              fontSize: '0.8rem',
              backgroundColor: 'var(--bg-leaf)',
              color: 'var(--primary-dark)',
              padding: '0.35rem 0.75rem',
              borderRadius: 'var(--radius-full)',
              display: 'flex',
              alignItems: 'center',
              gap: '0.35rem',
              fontWeight: 600,
            }}
          >
            <MapPin size={14} />
            <span>Active Location: {location.name}</span>
          </div>
        )}
      </div>

      <div className="card" style={{ padding: '1.25rem' }}>
        <ChatAssistant location={location} />
      </div>
    </div>
  );
}
