import React from 'react';
import {
  Sprout,
  CloudSun,
  ClipboardList,
  Camera,
  BookOpen,
  MessageSquare,
  MapPin,
  ChevronDown
} from 'lucide-react';

export default function Navbar({ activePage, setActivePage, location, onOpenLocationModal }) {
  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: Sprout },
    { id: 'weather', label: 'Weather Forecast', icon: CloudSun },
    { id: 'crop-assessment', label: 'Crop Assessment', icon: ClipboardList },
    { id: 'image-analysis', label: 'Image Analysis', icon: Camera },
    { id: 'advisories', label: 'Advisories', icon: BookOpen },
    { id: 'chat', label: 'AI Assistant', icon: MessageSquare },
  ];

  const locationDisplay = location
    ? `${location.name}${location.region ? `, ${location.region}` : ''}`
    : 'Select Location';

  return (
    <header style={{
      backgroundColor: '#ffffff',
      borderBottom: '1px solid var(--border-color)',
      position: 'sticky',
      top: 0,
      zIndex: 100,
      boxShadow: 'var(--shadow-sm)'
    }}>
      {/* Top branding bar */}
      <div style={{
        maxWidth: '1200px',
        margin: '0 auto',
        padding: '0.75rem 1rem',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '0.75rem',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
          <div style={{
            backgroundColor: 'var(--primary-green)',
            color: '#ffffff',
            padding: '0.45rem',
            borderRadius: 'var(--radius-sm)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}>
            <Sprout size={24} />
          </div>
          <div>
            <h1 style={{
              fontSize: '1.25rem',
              fontWeight: 700,
              color: 'var(--primary-dark)',
              lineHeight: 1.2,
              letterSpacing: '-0.3px',
            }}>
              KrishiRakshak AI
              <span style={{ fontSize: '0.85rem', fontWeight: 500, color: 'var(--text-muted)', marginLeft: '0.5rem' }}>
                (कृषिरक्षक)
              </span>
            </h1>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
              Agricultural Climate-Resilience Assistant • Maharashtra
            </p>
          </div>
        </div>

        {/* Location badge & selector */}
        <button
          onClick={onOpenLocationModal}
          className="btn btn-secondary"
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.4rem',
            padding: '0.4rem 0.8rem',
            fontSize: '0.85rem',
            borderRadius: 'var(--radius-full)',
          }}
          title="Click to search and change location"
        >
          <MapPin size={16} color="var(--primary-green)" />
          <span style={{ fontWeight: 600, maxWidth: '180px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
            {locationDisplay}
          </span>
          <ChevronDown size={14} color="var(--text-muted)" />
        </button>
      </div>

      {/* Navigation tabs */}
      <div style={{
        backgroundColor: '#ffffff',
        borderTop: '1px solid #f0f4f1',
      }}>
        <nav
          className="nav-tabs"
          style={{
            maxWidth: '1200px',
            margin: '0 auto',
            padding: '0 1rem',
            display: 'flex',
            gap: '0.25rem',
          }}
        >
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activePage === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActivePage(item.id)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.4rem',
                  padding: '0.7rem 0.9rem',
                  border: 'none',
                  borderBottom: `3px solid ${isActive ? 'var(--primary-green)' : 'transparent'}`,
                  backgroundColor: 'transparent',
                  color: isActive ? 'var(--primary-dark)' : 'var(--text-secondary)',
                  fontWeight: isActive ? 600 : 500,
                  fontSize: '0.875rem',
                  cursor: 'pointer',
                  transition: 'all 0.15s ease',
                }}
              >
                <Icon size={17} color={isActive ? 'var(--primary-green)' : 'currentColor'} />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>
      </div>
    </header>
  );
}
