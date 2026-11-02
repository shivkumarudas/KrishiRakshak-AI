import React, { useState, useEffect } from 'react';
import {
  BookOpen,
  RefreshCw,
  Info,
  Calendar,
  Building2,
  Globe,
  Filter,
  CheckCircle2,
  ShieldCheck,
  AlertTriangle,
} from 'lucide-react';
import { getAdvisories } from '../api';
import AdvisoryCard from '../components/AdvisoryCard';
import LoadingIndicator from '../components/LoadingIndicator';
import ErrorMessage from '../components/ErrorMessage';

const REGIONS = [
  { value: '', label: 'All Regions (सर्व भाग)' },
  { value: 'Entire Maharashtra', label: 'Entire Maharashtra (राज्यव्यापी मार्गदर्शन)' },
  { value: 'Marathwada', label: 'Marathwada (मराठवाडा - VNMKV, KVK Jalna)' },
  { value: 'Vidarbha', label: 'Vidarbha (विदर्भ - CICR, PDKV, KVK Yavatmal)' },
  { value: 'Western Maharashtra', label: 'Western Maharashtra (पश्चिम महाराष्ट्र - MPKV)' },
  { value: 'Central India', label: 'Central India (मध्य भारत - IISR Indore)' },
];

const STATUS_FILTERS = [
  { value: '', label: 'All Advisories (सर्व मार्गदर्शन)' },
  { value: 'verified_current_seasonal', label: 'Current Seasonal Only (चालू हंगाम)' },
  { value: 'verified_historical_reference', label: 'Historical Reference (ऐतिहासिक संदर्भ)' },
];

export default function AdvisoriesPage() {
  const [selectedCrop, setSelectedCrop] = useState('soybean');
  const [selectedStage, setSelectedStage] = useState('');
  const [selectedRegion, setSelectedRegion] = useState('');
  const [selectedStatus, setSelectedStatus] = useState('');
  const [advisoryData, setAdvisoryData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [checkingSources, setCheckingSources] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    loadAdvisories(selectedCrop, false, selectedStage, selectedRegion, selectedStatus);
  }, [selectedCrop, selectedStage, selectedRegion, selectedStatus]);

  const loadAdvisories = async (crop, checkSources, stage, region, status) => {
    if (checkSources) {
      setCheckingSources(true);
    } else {
      setLoading(true);
    }
    setError('');

    try {
      const data = await getAdvisories(
        crop,
        checkSources,
        stage || null,
        region || null,
        status || null,
        true
      );
      setAdvisoryData(data);
    } catch (err) {
      setError(err.message || 'Unable to load agricultural advisory catalogue.');
    } finally {
      setLoading(false);
      setCheckingSources(false);
    }
  };

  const advisories = advisoryData?.advisories || [];
  const sources = advisoryData?.sources || [];

  return (
    <div className="container" style={{ maxWidth: '980px' }}>
      {/* Header */}
      <div style={{ marginBottom: '1.5rem' }}>
        <h2
          style={{
            fontSize: '1.5rem',
            fontWeight: 700,
            color: 'var(--primary-dark)',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
          }}
        >
          <BookOpen size={28} /> Agricultural Knowledge Base &amp; Source Verification
        </h2>
        <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
          Verified agro-advisories from ICAR research institutes (IISR Indore, CICR Nagpur), Maharashtra State
          Agricultural Universities (VNMKV, PDKV, MPKV), Krishi Vigyan Kendras, and the State Agriculture Department.
        </p>
      </div>

      {/* Filter Card */}
      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            flexWrap: 'wrap',
            gap: '1rem',
            marginBottom: '1rem',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span style={{ fontWeight: 600, fontSize: '0.9rem' }}>Crop:</span>
            <div style={{ display: 'flex', gap: '0.4rem' }}>
              <button
                type="button"
                onClick={() => setSelectedCrop('soybean')}
                className={`btn ${selectedCrop === 'soybean' ? 'btn-primary' : 'btn-secondary'}`}
              >
                Soybean (सोयाबीन)
              </button>
              <button
                type="button"
                onClick={() => setSelectedCrop('cotton')}
                className={`btn ${selectedCrop === 'cotton' ? 'btn-primary' : 'btn-secondary'}`}
              >
                Cotton (कापूस)
              </button>
            </div>
          </div>

          <button
            type="button"
            onClick={() =>
              loadAdvisories(selectedCrop, true, selectedStage, selectedRegion, selectedStatus)
            }
            className="btn btn-outline"
            disabled={checkingSources || loading}
            style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}
          >
            <RefreshCw size={15} className={checkingSources ? 'spin-animation' : ''} />
            <span>{checkingSources ? 'Checking Official Portals...' : 'Verify Source Reachability'}</span>
          </button>
        </div>

        {/* Sub-Filters: Region, Stage, & Verification Status */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(210px, 1fr))',
            gap: '0.75rem',
            paddingTop: '0.75rem',
            borderTop: '1px solid var(--border-color)',
          }}
        >
          <div className="form-group" style={{ margin: 0 }}>
            <label className="form-label" style={{ fontSize: '0.8rem', fontWeight: 600 }}>
              <Globe size={12} style={{ display: 'inline', marginRight: '0.25rem' }} /> Agro-Climatic Zone
            </label>
            <select
              className="form-control"
              value={selectedRegion}
              onChange={(e) => setSelectedRegion(e.target.value)}
              style={{ height: '38px', fontSize: '0.85rem' }}
            >
              {REGIONS.map((r) => (
                <option key={r.value} value={r.value}>
                  {r.label}
                </option>
              ))}
            </select>
          </div>

          <div className="form-group" style={{ margin: 0 }}>
            <label className="form-label" style={{ fontSize: '0.8rem', fontWeight: 600 }}>
              <Filter size={12} style={{ display: 'inline', marginRight: '0.25rem' }} /> Growth Stage
            </label>
            <select
              className="form-control"
              value={selectedStage}
              onChange={(e) => setSelectedStage(e.target.value)}
              style={{ height: '38px', fontSize: '0.85rem' }}
            >
              <option value="">All Growth Stages (सर्व अवस्था)</option>
              {selectedCrop === 'soybean' ? (
                <>
                  <option value="Sowing">Sowing &amp; Early Vegetative</option>
                  <option value="Vegetative">Vegetative to Flowering</option>
                  <option value="Pod">Pod Filling / Maturity</option>
                </>
              ) : (
                <>
                  <option value="Squaring">Squaring and Flowering (45-60 DAS)</option>
                  <option value="Vegetative">Vegetative to Boll Development</option>
                  <option value="Drainage">Drainage &amp; Soil Moisture</option>
                </>
              )}
            </select>
          </div>

          <div className="form-group" style={{ margin: 0 }}>
            <label className="form-label" style={{ fontSize: '0.8rem', fontWeight: 600 }}>
              <ShieldCheck size={12} style={{ display: 'inline', marginRight: '0.25rem' }} /> Verification Filter
            </label>
            <select
              className="form-control"
              value={selectedStatus}
              onChange={(e) => setSelectedStatus(e.target.value)}
              style={{ height: '38px', fontSize: '0.85rem' }}
            >
              {STATUS_FILTERS.map((s) => (
                <option key={s.value} value={s.value}>
                  {s.label}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {loading && <LoadingIndicator message="Loading verified advisories from knowledge base..." />}

      {error && <ErrorMessage message={error} style={{ marginBottom: '1.5rem' }} />}

      {/* Advisory Principles Callout */}
      <div className="alert alert-info" style={{ marginBottom: '1.5rem' }}>
        <Info size={20} style={{ flexShrink: 0 }} />
        <div style={{ fontSize: '0.875rem', lineHeight: 1.45 }}>
          <strong>Knowledge Verification Principle:</strong> Network reachability is separate from content
          verification. A reachable institutional web URL confirms server availability, but is{' '}
          <em>not proof</em> that an advisory is current for this season. Always check the publication date, validity
          period, and agro-climatic applicability before adopting recommendations.
        </div>
      </div>

      {/* Source Reachability Results (When Checked) */}
      {advisoryData?.source_reachability && (
        <div
          className="card"
          style={{
            marginBottom: '1.5rem',
            backgroundColor: '#f9fbf9',
            border: '1px solid #c8e6c9',
          }}
        >
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              flexWrap: 'wrap',
              gap: '0.5rem',
              marginBottom: '0.5rem',
            }}
          >
            <h4
              style={{
                fontSize: '0.95rem',
                fontWeight: 700,
                color: 'var(--primary-dark)',
                margin: 0,
                display: 'flex',
                alignItems: 'center',
                gap: '0.35rem',
              }}
            >
              <Globe size={16} /> Official Web Portal Connectivity Report
            </h4>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              Checked at: {advisoryData.source_reachability.checked_at?.slice(0, 19).replace('T', ' ')}
            </span>
          </div>

          <p style={{ fontSize: '0.825rem', color: 'var(--text-secondary)', marginBottom: '0.75rem' }}>
            {advisoryData.source_reachability.warning}
          </p>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            {advisoryData.source_reachability.sources?.map((src, i) => (
              <div
                key={i}
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  padding: '0.55rem 0.75rem',
                  backgroundColor: '#ffffff',
                  borderRadius: 'var(--radius-sm)',
                  border: '1px solid var(--border-color)',
                  fontSize: '0.85rem',
                }}
              >
                <div>
                  <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
                    {src.source_name || src.name}
                  </div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                    {src.official_url} {src.redirected ? '(Redirected)' : ''}
                  </div>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  {src.http_status && (
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                      HTTP {src.http_status}
                    </span>
                  )}
                  <span className={`badge ${src.reachable ? 'badge-green' : 'badge-amber'}`}>
                    {src.reachable ? '✓ Server Online' : '✗ Unreachable'}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Verified Advisories List */}
      <div style={{ marginBottom: '2rem' }}>
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            flexWrap: 'wrap',
            gap: '0.5rem',
            marginBottom: '1rem',
          }}
        >
          <h3 style={{ fontSize: '1.15rem', fontWeight: 700, color: 'var(--primary-dark)', margin: 0 }}>
            {selectedCrop === 'soybean' ? 'Soybean (सोयाबीन)' : 'Cotton (कापूस)'} Bulletins ({advisories.length})
          </h3>
          <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            Ranked by Regional Relevance &amp; Freshness
          </span>
        </div>

        {advisories.length > 0 ? (
          advisories.map((adv, idx) => (
            <AdvisoryCard key={adv.source_id || adv.id || idx} advisory={adv} type="advisory" />
          ))
        ) : (
          <div
            className="card"
            style={{
              textAlign: 'center',
              padding: '2rem',
              color: 'var(--text-secondary)',
            }}
          >
            No advisories match the selected filters. Try selecting &quot;All Regions&quot; or &quot;All Growth Stages&quot;.
          </div>
        )}
      </div>

      {/* Official Catalog Sources List */}
      {sources.length > 0 && (
        <div style={{ marginBottom: '2rem' }}>
          <h3 style={{ fontSize: '1.15rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '1rem' }}>
            Official Research Sources &amp; Institutional Portals ({sources.length})
          </h3>
          {sources.map((src, idx) => (
            <AdvisoryCard key={src.source_id || idx} advisory={src} type="source" />
          ))}
        </div>
      )}
    </div>
  );
}
