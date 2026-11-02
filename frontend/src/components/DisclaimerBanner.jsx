import React from 'react';
import { AlertTriangle } from 'lucide-react';

export default function DisclaimerBanner({ text }) {
  const defaultText = (
    "Weather forecasts can change. Weather-based guidance is general information and " +
    "does not constitute a verified crop diagnosis or chemical prescription. Always consult your " +
    "local Krishi Vigyan Kendra (KVK) or Taluka Agriculture Officer before taking action."
  );

  return (
    <div className="alert alert-warning" style={{ marginTop: '1rem', marginBottom: '1rem' }}>
      <AlertTriangle size={20} style={{ flexShrink: 0, marginTop: '2px' }} />
      <div>
        <strong style={{ display: 'block', marginBottom: '0.2rem' }}>Agricultural Advisory Notice:</strong>
        <span>{text || defaultText}</span>
      </div>
    </div>
  );
}
