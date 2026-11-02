import React from 'react';
import { AlertCircle, AlertTriangle, RefreshCw } from 'lucide-react';

/**
 * Reusable Error and Warning Message Component.
 * Supports accessible roles, customizable types, and an optional retry callback.
 */
export default function ErrorMessage({
  message,
  type = 'error',
  onRetry = null,
  style = {},
}) {
  if (!message) return null;

  const isWarning = type === 'warning';
  const Icon = isWarning ? AlertTriangle : AlertCircle;
  const alertClass = isWarning ? 'alert alert-warning' : 'alert alert-danger';

  return (
    <div
      className={alertClass}
      role="alert"
      aria-live="assertive"
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '0.75rem',
        ...style,
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flex: 1 }}>
        <Icon size={20} style={{ flexShrink: 0 }} aria-hidden="true" />
        <span style={{ fontSize: '0.9rem', lineHeight: 1.4 }}>{message}</span>
      </div>

      {onRetry && (
        <button
          onClick={onRetry}
          className="btn btn-secondary"
          style={{ fontSize: '0.8rem', padding: '0.35rem 0.75rem', display: 'flex', alignItems: 'center', gap: '0.35rem' }}
          aria-label="Retry action"
        >
          <RefreshCw size={14} /> Retry
        </button>
      )}
    </div>
  );
}
