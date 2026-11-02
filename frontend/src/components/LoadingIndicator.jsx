import React from 'react';
import { Loader2 } from 'lucide-react';

/**
 * Accessible Loading Indicator with spinner and customizable screen-reader text.
 */
export default function LoadingIndicator({
  message = 'Loading...',
  size = 28,
  compact = false,
  style = {},
}) {
  if (compact) {
    return (
      <div
        role="status"
        aria-live="polite"
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '0.5rem',
          fontSize: '0.875rem',
          color: 'var(--text-secondary)',
          ...style,
        }}
      >
        <Loader2 size={size} className="spin-animation" style={{ color: 'var(--primary-color)' }} aria-hidden="true" />
        <span>{message}</span>
      </div>
    );
  }

  return (
    <div
      role="status"
      aria-live="polite"
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '2.5rem 1rem',
        gap: '0.75rem',
        color: 'var(--text-secondary)',
        ...style,
      }}
    >
      <Loader2 size={size} className="spin-animation" style={{ color: 'var(--primary-color)' }} aria-hidden="true" />
      <span style={{ fontSize: '0.925rem', fontWeight: 500 }}>{message}</span>
    </div>
  );
}
