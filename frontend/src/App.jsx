import React, { useState } from 'react';
import Navbar from './components/Navbar';
import LocationModal from './components/LocationModal';
import DashboardPage from './pages/DashboardPage';
import WeatherPage from './pages/WeatherPage';
import CropAssessmentPage from './pages/CropAssessmentPage';
import ImageAnalysisPage from './pages/ImageAnalysisPage';
import AdvisoriesPage from './pages/AdvisoriesPage';
import ChatAssistantPage from './pages/ChatAssistantPage';

export default function App() {
  const [activePage, setActivePage] = useState('dashboard');
  const [isLocationModalOpen, setIsLocationModalOpen] = useState(false);

  // Default confirmed location: Pune, Maharashtra
  const [location, setLocation] = useState({
    name: 'Pune',
    region: 'Maharashtra',
    country: 'India',
    latitude: 18.5204,
    longitude: 73.8567,
  });

  // Keep track of recent crop assessment
  const [recentAssessment, setRecentAssessment] = useState(null);

  const renderPage = () => {
    switch (activePage) {
      case 'dashboard':
        return (
          <DashboardPage
            location={location}
            onOpenLocationModal={() => setIsLocationModalOpen(true)}
            setActivePage={setActivePage}
            recentAssessment={recentAssessment}
          />
        );
      case 'weather':
        return (
          <WeatherPage
            location={location}
            setLocation={setLocation}
          />
        );
      case 'crop-assessment':
        return (
          <CropAssessmentPage
            onSaveAssessment={(data) => setRecentAssessment(data)}
          />
        );
      case 'image-analysis':
        return <ImageAnalysisPage />;
      case 'advisories':
        return <AdvisoriesPage />;
      case 'chat':
        return <ChatAssistantPage location={location} />;
      default:
        return (
          <DashboardPage
            location={location}
            onOpenLocationModal={() => setIsLocationModalOpen(true)}
            setActivePage={setActivePage}
            recentAssessment={recentAssessment}
          />
        );
    }
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <Navbar
        activePage={activePage}
        setActivePage={setActivePage}
        location={location}
        onOpenLocationModal={() => setIsLocationModalOpen(true)}
      />

      <main style={{ flex: 1, padding: '1rem 0' }}>
        {renderPage()}
      </main>

      <footer style={{
        backgroundColor: '#ffffff',
        borderTop: '1px solid var(--border-color)',
        padding: '1.5rem 1rem',
        marginTop: 'auto',
        fontSize: '0.85rem',
        color: 'var(--text-muted)',
      }}>
        <div style={{
          maxWidth: '1200px',
          margin: '0 auto',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '1rem',
        }}>
          <div>
            <strong style={{ color: 'var(--primary-dark)' }}>KrishiRakshak AI (कृषिरक्षक)</strong> — Agricultural Climate Resilience
            <div style={{ fontSize: '0.75rem', marginTop: '0.2rem' }}>
              Built for farmers in Maharashtra, India • Open-Meteo & Official ICAR Sources
            </div>
          </div>
          <div style={{ fontSize: '0.75rem', textAlign: 'right' }}>
            General guidance only • Not a substitute for local agricultural officer advice
          </div>
        </div>
      </footer>

      <LocationModal
        isOpen={isLocationModalOpen}
        onClose={() => setIsLocationModalOpen(false)}
        onSelectLocation={(loc) => setLocation(loc)}
        currentLocation={location}
      />
    </div>
  );
}
