import React from 'react';
import LoadingIndicator from './LoadingIndicator';

/**
 * Backward-compatible LoadingSpinner re-exporting LoadingIndicator.
 */
export default function LoadingSpinner(props) {
  return <LoadingIndicator {...props} />;
}
