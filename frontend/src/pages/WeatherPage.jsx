import React, { useState, useEffect } from 'react';
import { CloudSun, MapPin, RefreshCw, Info, CloudRain, Droplets } from 'lucide-react';
import { getWeather } from '../api';
import WeatherCard from '../components/WeatherCard';
import LocationSearch from '../components/LocationSearch';
import LoadingIndicator from '../components/LoadingIndicator';
import ErrorMessage from '../components/ErrorMessage';
import DisclaimerBanner from '../components/DisclaimerBanner';

export default function WeatherPage({ location, setLocation }) {
  const [forecast, setForecast] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [showSearch, setShowSearch] = useState(false);

  useEffect(() => {
    if (location) {
      loadForecast(location);
    }
  }, [location]);

  const loadForecast = async (loc, force = false) => {
    setLoading(true);
    setError('');
    try {
      const data = await getWeather(loc.latitude, loc.longitude, loc.name, force);
      setForecast(data);
    } catch (err) {
      setError(err.message || 'Unable to retrieve weather forecast.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container">
      {/* Page Header */}
      <div style={{ marginBottom: '1.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.75rem' }}>
        <div>
          <h2 style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--primary-dark)', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <CloudSun size={28} /> Weather Forecast &amp; Farming Guidance
          </h2>
          <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
            Real-time 3-day meteorological forecast from Open-Meteo with rule-based agricultural precautions.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <button
            type="button"
            onClick={() => setShowSearch(!showSearch)}
            className="btn btn-outline"
            style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}
          >
            <MapPin size={16} />
            <span>{showSearch ? 'Hide Search' : 'Change Location'}</span>
          </button>
          <button
            type="button"
            onClick={() => location && loadForecast(location, true)}
            className="btn btn-secondary"
            disabled={loading}
            style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}
          >
            <RefreshCw size={15} className={loading ? 'spin-animation' : ''} />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* Expandable Location Search */}
      {showSearch && (
        <div className="card" style={{ marginBottom: '1.5rem', backgroundColor: '#f9fbf9', border: '1px solid #c8e6c9' }}>
          <h4 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--primary-dark)', marginBottom: '0.75rem' }}>
            Search &amp; Confirm Farm Location
          </h4>
          <LocationSearch
            onSelectLocation={(place) => {
              setLocation(place);
              setShowSearch(false);
            }}
            onCancel={() => setShowSearch(false)}
          />
        </div>
      )}

      {/* Confirmed Location Badge Card */}
      {location && (
        <div
          className="card"
          style={{
            marginBottom: '1.5rem',
            padding: '1rem 1.25rem',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            flexWrap: 'wrap',
            gap: '0.75rem',
            backgroundColor: '#ffffff',
          }}
        >
          <div>
            <div style={{ fontSize: '0.75rem', textTransform: 'uppercase', color: 'var(--text-muted)' }}>Confirmed Location</div>
            <div style={{ fontSize: '1.2rem', fontWeight: 700, color: 'var(--primary-dark)' }}>
              {location.name}
            </div>
            <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
              {[location.region, location.country].filter(Boolean).join(', ')} ({location.latitude?.toFixed(2)}°N, {location.longitude?.toFixed(2)}°E)
            </div>
          </div>

          <div style={{ textAlign: 'right', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            <div>Data Source: <strong>{forecast?.source || 'Open-Meteo'}</strong></div>
            <div>Forecast Horizon: <strong>3 Days</strong></div>
          </div>
        </div>
      )}

      {loading && <LoadingIndicator message="Fetching latest weather forecast and agricultural guidance..." />}

      {error && (
        <ErrorMessage
          message={error}
          onRetry={() => location && loadForecast(location)}
          style={{ marginBottom: '1.5rem' }}
        />
      )}

      {/* 3-Day Forecast Cards */}
      {forecast && !loading && (
        <>
          <div className="grid-3" style={{ marginBottom: '1.5rem' }}>
            {forecast.dates.map((dateStr, idx) => (
              <WeatherCard
                key={dateStr}
                date={dateStr}
                rainProbability={forecast.rain_probability_percent[idx]}
                rainfall={forecast.rainfall_mm[idx]}
                weatherCode={forecast.weather_codes[idx]}
                guidance={forecast.daily_guidance?.[idx]}
                source={forecast.source}
              />
            ))}
          </div>

          <DisclaimerBanner />
        </>
      )}
    </div>
  );
}
