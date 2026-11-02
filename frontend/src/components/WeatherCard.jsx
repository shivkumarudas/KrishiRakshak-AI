import React from 'react';
import { CloudRain, Sun, Cloud, AlertCircle, Droplets, Wind } from 'lucide-react';

function getWeatherDescription(code) {
  if (code === 0) return { text: 'Clear Sky', icon: Sun, color: '#f57f17' };
  if (code >= 1 && code <= 3) return { text: 'Partly Cloudy', icon: Cloud, color: '#78909c' };
  if (code >= 45 && code <= 48) return { text: 'Fog / Mist', icon: Wind, color: '#90a4ae' };
  if (code >= 51 && code <= 55) return { text: 'Drizzle', icon: CloudRain, color: '#42a5f5' };
  if (code >= 61 && code <= 65) return { text: 'Rain', icon: CloudRain, color: '#1e88e5' };
  if (code >= 80 && code <= 82) return { text: 'Rain Showers', icon: CloudRain, color: '#1565c0' };
  if (code >= 95) return { text: 'Thunderstorm', icon: AlertCircle, color: '#d32f2f' };
  return { text: 'Overcast', icon: Cloud, color: '#78909c' };
}

export default function WeatherCard({ guidance, isToday = false }) {
  if (!guidance) return null;

  const { date, rain_probability_percent, rainfall_mm, weather_code, risks, advice } = guidance;
  const weatherInfo = getWeatherDescription(weather_code);
  const Icon = weatherInfo.icon;

  const rainProb = rain_probability_percent !== null && rain_probability_percent !== undefined
    ? rain_probability_percent
    : null;

  const rainAmount = rainfall_mm !== null && rainfall_mm !== undefined
    ? rainfall_mm
    : null;

  return (
    <div className="card" style={{
      borderTop: isToday ? '4px solid var(--primary-green)' : '1px solid var(--border-color)',
      position: 'relative',
      display: 'flex',
      flexDirection: 'column',
      justifyContent: 'space-between',
    }}>
      <div>
        {/* Date header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
          <div>
            <span style={{ fontSize: '0.8rem', textTransform: 'uppercase', color: 'var(--text-muted)', fontWeight: 600 }}>
              {isToday ? 'Today / Day 1' : 'Forecast'}
            </span>
            <h4 style={{ fontSize: '1.05rem', fontWeight: 600, color: 'var(--text-primary)' }}>
              {date}
            </h4>
          </div>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.35rem',
            padding: '0.3rem 0.6rem',
            borderRadius: 'var(--radius-sm)',
            backgroundColor: '#f1f5f2',
          }}>
            <Icon size={18} color={weatherInfo.color} />
            <span style={{ fontSize: '0.8rem', fontWeight: 500, color: 'var(--text-secondary)' }}>
              {weatherInfo.text}
            </span>
          </div>
        </div>

        {/* Rain indicators */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: '1fr 1fr',
          gap: '0.5rem',
          backgroundColor: 'var(--bg-leaf)',
          padding: '0.75rem',
          borderRadius: 'var(--radius-sm)',
          marginBottom: '0.75rem',
        }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.3rem', fontSize: '0.75rem', color: 'var(--primary-dark)' }}>
              <CloudRain size={14} /> Rain Probability
            </div>
            <div style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--primary-dark)', marginTop: '0.15rem' }}>
              {rainProb !== null ? `${rainProb}%` : 'N/A'}
            </div>
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.3rem', fontSize: '0.75rem', color: 'var(--primary-dark)' }}>
              <Droplets size={14} /> Expected Rain
            </div>
            <div style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--primary-dark)', marginTop: '0.15rem' }}>
              {rainAmount !== null ? `${rainAmount} mm` : 'N/A'}
            </div>
          </div>
        </div>

        {/* Risks */}
        {risks && risks.length > 0 && (
          <div style={{ marginBottom: '0.75rem' }}>
            <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--warning-text)', display: 'block', marginBottom: '0.25rem' }}>
              Weather Factors:
            </span>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.3rem' }}>
              {risks.map((risk, idx) => (
                <span key={idx} className="badge badge-amber" style={{ fontSize: '0.7rem' }}>
                  {risk}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Agricultural Advice */}
        {advice && advice.length > 0 && (
          <div style={{ marginTop: '0.5rem' }}>
            <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-secondary)', display: 'block', marginBottom: '0.35rem' }}>
              🌱 General Farming Precautions:
            </span>
            <ul style={{ paddingLeft: '1.2rem', fontSize: '0.85rem', color: 'var(--text-primary)', lineHeight: 1.4 }}>
              {advice.map((item, idx) => (
                <li key={idx} style={{ marginBottom: '0.25rem' }}>{item}</li>
              ))}
            </ul>
          </div>
        )}
      </div>

      <div style={{ marginTop: '0.75rem', paddingTop: '0.5rem', borderTop: '1px dashed var(--border-color)', fontSize: '0.72rem', color: 'var(--text-muted)' }}>
        Source: Open-Meteo • Advisory only
      </div>
    </div>
  );
}
