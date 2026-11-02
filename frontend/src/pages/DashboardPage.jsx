import React, { useState, useEffect } from 'react';
import {
  CloudSun,
  ClipboardList,
  Camera,
  BookOpen,
  MessageSquare,
  ArrowRight,
  MapPin,
  AlertCircle,
  Sprout,
  CheckCircle2,
  Calendar
} from 'lucide-react';
import { getWeather, getAdvisories } from '../api';
import WeatherCard from '../components/WeatherCard';
import LoadingSpinner from '../components/LoadingSpinner';
import DisclaimerBanner from '../components/DisclaimerBanner';

export default function DashboardPage({ location, onOpenLocationModal, setActivePage, recentAssessment }) {
  const [weatherData, setWeatherData] = useState(null);
  const [weatherLoading, setWeatherLoading] = useState(false);
  const [weatherError, setWeatherError] = useState('');
  const [soybeanAdvisory, setSoybeanAdvisory] = useState(null);
  const [cottonAdvisory, setCottonAdvisory] = useState(null);

  useEffect(() => {
    if (location) {
      loadWeather();
    }
  }, [location]);

  useEffect(() => {
    // Load overview advisories
    getAdvisories('soybean').then(setSoybeanAdvisory).catch(() => {});
    getAdvisories('cotton').then(setCottonAdvisory).catch(() => {});
  }, []);

  const loadWeather = async () => {
    if (!location) return;
    setWeatherLoading(true);
    setWeatherError('');
    try {
      const data = await getWeather(location.latitude, location.longitude, location.name);
      setWeatherData(data);
    } catch (err) {
      setWeatherError(err.message || 'Unable to retrieve weather data.');
    } finally {
      setWeatherLoading(false);
    }
  };

  return (
    <div className="container">
      {/* Hero Welcome Banner */}
      <div className="card" style={{
        background: 'linear-gradient(135deg, #1b5e20 0%, #2e7d32 100%)',
        color: '#ffffff',
        padding: '1.75rem',
        marginBottom: '1.5rem',
        borderRadius: 'var(--radius-lg)',
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem' }}>
          <div>
            <span className="badge" style={{ backgroundColor: 'rgba(255,255,255,0.2)', color: '#ffffff', marginBottom: '0.5rem' }}>
              🌾 Maharashtra Farmer Assistant
            </span>
            <h2 style={{ fontSize: '1.65rem', fontWeight: 700, margin: '0.25rem 0 0.5rem 0' }}>
              Welcome to KrishiRakshak AI
            </h2>
            <p style={{ fontSize: '0.95rem', opacity: 0.9, maxWidth: '650px', lineHeight: 1.5 }}>
              Your agricultural climate resilience companion. Monitor local 3-day rainfall,
              record crop symptoms without guesswork, and access verified government advisories.
            </p>
          </div>

          <div style={{
            backgroundColor: 'rgba(255, 255, 255, 0.15)',
            backdropFilter: 'blur(5px)',
            padding: '0.85rem 1.1rem',
            borderRadius: 'var(--radius-md)',
            border: '1px solid rgba(255,255,255,0.25)',
          }}>
            <div style={{ fontSize: '0.75rem', textTransform: 'uppercase', opacity: 0.85 }}>Confirmed Location</div>
            <div style={{ fontSize: '1.1rem', fontWeight: 700, margin: '0.15rem 0' }}>
              {location ? location.name : 'Not set'}
            </div>
            <div style={{ fontSize: '0.8rem', opacity: 0.85, marginBottom: '0.5rem' }}>
              {location ? `${location.region || 'Maharashtra'}, ${location.country || 'India'}` : 'Click to select'}
            </div>
            <button
              onClick={onOpenLocationModal}
              className="btn btn-secondary"
              style={{ fontSize: '0.8rem', padding: '0.35rem 0.75rem', backgroundColor: '#ffffff', color: 'var(--primary-dark)', fontWeight: 600 }}
            >
              <MapPin size={14} /> Change Location
            </button>
          </div>
        </div>
      </div>

      {/* Weather Forecast Section */}
      <div style={{ marginBottom: '2rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <div>
            <h3 style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--primary-dark)', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <CloudSun size={24} /> 3-Day Weather & Rainfall Forecast
            </h3>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
              Actual precipitation probability and volume for {location ? location.name : 'your farm'}.
            </p>
          </div>
          <button
            onClick={() => setActivePage('weather')}
            className="btn btn-outline"
            style={{ fontSize: '0.85rem' }}
          >
            Full Weather Details <ArrowRight size={16} />
          </button>
        </div>

        {weatherLoading && <LoadingSpinner message="Retrieving Open-Meteo weather forecast..." />}

        {weatherError && (
          <div className="alert alert-danger">
            <AlertCircle size={20} />
            <div>
              <strong>Weather Service Notice:</strong> {weatherError}
              <button onClick={loadWeather} className="btn btn-secondary" style={{ marginLeft: '1rem', padding: '0.2rem 0.6rem', fontSize: '0.75rem' }}>
                Retry
              </button>
            </div>
          </div>
        )}

        {weatherData && weatherData.daily_guidance && (
          <div className="grid-3">
            {weatherData.daily_guidance.map((day, idx) => (
              <WeatherCard key={day.date} guidance={day} isToday={idx === 0} />
            ))}
          </div>
        )}
      </div>

      {/* Quick Action Cards Grid */}
      <div style={{ marginBottom: '2rem' }}>
        <h3 style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--primary-dark)', marginBottom: '1rem' }}>
          🌾 Agricultural Tools
        </h3>

        <div className="grid-3">
          {/* Card 1: Crop Assessment */}
          <div className="card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
                <div style={{ padding: '0.5rem', backgroundColor: 'var(--bg-leaf)', borderRadius: 'var(--radius-sm)', color: 'var(--primary-green)' }}>
                  <ClipboardList size={22} />
                </div>
                <h4 style={{ fontSize: '1.05rem', fontWeight: 600 }}>Crop Assessment</h4>
              </div>
              <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', marginBottom: '1rem' }}>
                Record symptoms on Soybean or Cotton. Receive field inspection checklists and safety guidance without chemical dosing.
              </p>
            </div>
            <button onClick={() => setActivePage('crop-assessment')} className="btn btn-outline" style={{ width: '100%' }}>
              Start Assessment <ArrowRight size={16} />
            </button>
          </div>

          {/* Card 2: Image Analysis */}
          <div className="card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
                <div style={{ padding: '0.5rem', backgroundColor: '#e1f5fe', borderRadius: 'var(--radius-sm)', color: '#0288d1' }}>
                  <Camera size={22} />
                </div>
                <h4 style={{ fontSize: '1.05rem', fontWeight: 600 }}>Crop Image Analysis</h4>
              </div>
              <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', marginBottom: '1rem' }}>
                Upload photos of affected leaves or bolls. Validates format and checks for visible pest signs.
              </p>
            </div>
            <button onClick={() => setActivePage('image-analysis')} className="btn btn-outline" style={{ width: '100%' }}>
              Upload Image <ArrowRight size={16} />
            </button>
          </div>

          {/* Card 3: AI Chat Assistant */}
          <div className="card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
                <div style={{ padding: '0.5rem', backgroundColor: '#fff3e0', borderRadius: 'var(--radius-sm)', color: '#ef6c00' }}>
                  <MessageSquare size={22} />
                </div>
                <h4 style={{ fontSize: '1.05rem', fontWeight: 600 }}>AI Farming Assistant</h4>
              </div>
              <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', marginBottom: '1rem' }}>
                Ask questions in Marathi, Hindi, or English. Receives answers powered by Gemini with weather context.
              </p>
            </div>
            <button onClick={() => setActivePage('chat')} className="btn btn-outline" style={{ width: '100%' }}>
              Ask Question <ArrowRight size={16} />
            </button>
          </div>
        </div>
      </div>

      {/* Recent Assessment Callout (if present) */}
      {recentAssessment && (
        <div className="card" style={{ marginBottom: '2rem', borderLeft: '4px solid var(--primary-green)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '0.5rem' }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: 'var(--primary-green)', fontWeight: 600, fontSize: '0.85rem' }}>
                <CheckCircle2 size={18} /> Recent Crop Assessment
              </div>
              <h4 style={{ fontSize: '1.1rem', fontWeight: 600, margin: '0.2rem 0' }}>
                {recentAssessment.crop} ({recentAssessment.growth_stage})
              </h4>
              <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
                <strong>Reported:</strong> {recentAssessment.reported_symptoms}
                {recentAssessment.affected_part && recentAssessment.affected_part !== 'unknown' && ` • Part: ${recentAssessment.affected_part}`}
              </p>
            </div>
            <button onClick={() => setActivePage('crop-assessment')} className="btn btn-secondary" style={{ fontSize: '0.8rem' }}>
              View Details
            </button>
          </div>
        </div>
      )}

      {/* Agricultural Advisory Preview */}
      <div style={{ marginBottom: '1.5rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <div>
            <h3 style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--primary-dark)', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <BookOpen size={24} /> Official Agricultural Sources
            </h3>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
              Curated official guidance from ICAR, KVKs, and Agricultural Universities in Maharashtra.
            </p>
          </div>
          <button onClick={() => setActivePage('advisories')} className="btn btn-outline" style={{ fontSize: '0.85rem' }}>
            View Catalogue <ArrowRight size={16} />
          </button>
        </div>

        <div className="grid-2">
          {soybeanAdvisory && (
            <div className="card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                <span className="badge badge-green">Soybean (सोयाबीन)</span>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{soybeanAdvisory.region}</span>
              </div>
              <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.75rem' }}>
                Official bulletins from ICAR - Indian Institute of Soybean Research and weekly state advisories.
              </p>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                {soybeanAdvisory.sources?.length || 0} registered official reference pages
              </div>
            </div>
          )}

          {cottonAdvisory && (
            <div className="card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                <span className="badge badge-green">Cotton (कापूस)</span>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{cottonAdvisory.region}</span>
              </div>
              <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.75rem' }}>
                Regional Kharif agro-advisories from ICAR and Maharashtra Agriculture Department.
              </p>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                {cottonAdvisory.sources?.length || 0} registered official reference pages
              </div>
            </div>
          )}
        </div>
      </div>

      <DisclaimerBanner />
    </div>
  );
}
