import React from 'react';
import { MapPin, X } from 'lucide-react';
import LocationSearch from './LocationSearch';

/**
 * Modal dialog for changing farm location using LocationSearch.
 */
export default function LocationModal({ isOpen, onClose, onSelectLocation, currentLocation }) {
  if (!isOpen) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="location-modal-title"
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(0, 0, 0, 0.5)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 1000,
        padding: '1rem',
      }}
    >
      <div
        className="card"
        style={{
          maxWidth: '560px',
          width: '100%',
          maxHeight: '90vh',
          overflowY: 'auto',
          position: 'relative',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <h3 id="location-modal-title" className="card-title" style={{ margin: 0 }}>
            <MapPin size={22} style={{ color: 'var(--primary-color)' }} /> Select Your Farm Location
          </h3>
          <button
            onClick={onClose}
            className="btn btn-secondary"
            style={{ padding: '0.35rem', borderRadius: '50%', minWidth: 'auto', width: '32px', height: '32px' }}
            aria-label="Close location dialog"
          >
            <X size={18} />
          </button>
        </div>

        <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', marginBottom: '1.25rem' }}>
          Enter your village, taluka, or district in Maharashtra to receive verified Open-Meteo rainfall forecasts and weather-based guidance.
        </p>

        <LocationSearch
          onSelectLocation={(place) => {
            onSelectLocation(place);
            onClose();
          }}
          onCancel={onClose}
        />

        {currentLocation && (
          <div style={{ marginTop: '1.25rem', paddingTop: '1rem', borderTop: '1px solid var(--border-color)', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
            Currently confirmed: <strong>{currentLocation.name}</strong> ({currentLocation.region || 'Maharashtra'})
          </div>
        )}
      </div>
    </div>
  );
}
