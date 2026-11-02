import React, { useState } from 'react';
import { Search, MapPin, Check, AlertCircle, Loader2 } from 'lucide-react';
import { searchLocations } from '../api';

/**
 * Reusable Location Search Component.
 * Allows searching by village, taluka, or district name using the geocoding endpoint.
 */
export default function LocationSearch({ onSelectLocation, initialQuery = '', onCancel = null }) {
  const [query, setQuery] = useState(initialQuery);
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [hasSearched, setHasSearched] = useState(false);

  const handleSearch = async (e) => {
    if (e) e.preventDefault();
    const cleanQuery = query.trim();
    if (!cleanQuery) return;

    setLoading(true);
    setError('');
    setHasSearched(true);

    try {
      const data = await searchLocations(cleanQuery);
      setResults(data.results || []);
    } catch (err) {
      setError(err.message || 'Unable to search for this location. Please check network connection.');
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Escape' && onCancel) {
      onCancel();
    }
  };

  return (
    <div className="location-search-component" onKeyDown={handleKeyDown}>
      <form onSubmit={handleSearch} style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem' }}>
        <div style={{ position: 'relative', flex: 1 }}>
          <MapPin
            size={18}
            style={{
              position: 'absolute',
              left: '0.85rem',
              top: '50%',
              transform: 'translateY(-50%)',
              color: 'var(--text-muted)',
            }}
            aria-hidden="true"
          />
          <input
            type="text"
            className="form-control"
            style={{ paddingLeft: '2.5rem' }}
            placeholder="Enter village, taluka, or district (e.g. Pune, Latur, Nagpur)..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            autoFocus
            aria-label="Location search input"
          />
        </div>
        <button
          type="submit"
          className="btn btn-primary"
          disabled={loading || !query.trim()}
          style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', minWidth: '100px' }}
        >
          {loading ? (
            <Loader2 size={16} className="spin-animation" />
          ) : (
            <Search size={16} />
          )}
          <span>Search</span>
        </button>
      </form>

      {/* Error state */}
      {error && (
        <div className="alert alert-danger" style={{ marginBottom: '1rem' }} role="alert">
          <AlertCircle size={16} />
          <span>{error}</span>
        </div>
      )}

      {/* Results listing */}
      {results.length > 0 && (
        <div>
          <div style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-secondary)', textTransform: 'uppercase', marginBottom: '0.5rem' }}>
            Found {results.length} locations — Select to confirm:
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', maxHeight: '250px', overflowY: 'auto' }}>
            {results.map((place, idx) => (
              <div
                key={`${place.latitude}-${place.longitude}-${idx}`}
                onClick={() => onSelectLocation(place)}
                tabIndex={0}
                role="button"
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    onSelectLocation(place);
                  }
                }}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '0.75rem 1rem',
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid var(--border-color)',
                  backgroundColor: '#ffffff',
                  cursor: 'pointer',
                  transition: 'all 0.15s ease',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.borderColor = 'var(--primary-color)';
                  e.currentTarget.style.backgroundColor = 'var(--bg-leaf)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.borderColor = 'var(--border-color)';
                  e.currentTarget.style.backgroundColor = '#ffffff';
                }}
              >
                <div>
                  <div style={{ fontWeight: 600, color: 'var(--text-primary)', fontSize: '0.95rem' }}>
                    {place.name}
                  </div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                    {[place.region, place.country].filter(Boolean).join(', ')}
                  </div>
                </div>
                <button
                  type="button"
                  className="btn btn-secondary"
                  style={{ fontSize: '0.75rem', padding: '0.3rem 0.6rem', display: 'flex', alignItems: 'center', gap: '0.25rem' }}
                  onClick={(e) => {
                    e.stopPropagation();
                    onSelectLocation(place);
                  }}
                  aria-label={`Select ${place.name}`}
                >
                  <Check size={14} /> Select
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Empty result state */}
      {hasSearched && !loading && results.length === 0 && !error && (
        <div style={{ textAlign: 'center', padding: '1.5rem', color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
          No locations found matching &quot;<strong>{query}</strong>&quot;. Please check spelling or try district name.
        </div>
      )}
    </div>
  );
}
