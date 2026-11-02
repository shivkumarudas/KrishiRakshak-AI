import React from 'react';
import {
  ShieldCheck,
  ExternalLink,
  Calendar,
  Building2,
  AlertTriangle,
  FileText,
  Clock,
  MapPin,
  CheckCircle2,
  Info,
} from 'lucide-react';

const SOURCE_TYPE_LABELS = {
  icar_institute: 'ICAR Research Institute (केंद्रीय संस्था)',
  state_agricultural_university: 'State Agricultural University (कृषी विद्यापीठ)',
  krishi_vigyan_kendra: 'Krishi Vigyan Kendra (KVK / कृषी विज्ञान केंद्र)',
  state_agriculture_department: 'State Agriculture Dept (कृषी विभाग, महाराष्ट्र)',
  official_research_institute: 'Official Research Authority',
};

/**
 * Reusable Advisory & Source Card Component.
 * Strictly separates current seasonal guidance from historical references,
 * displays institutional source types, and explicitly prohibits adopting
 * outdated chemical doses from historical bulletins.
 */
export default function AdvisoryCard({ advisory, type = 'advisory' }) {
  if (!advisory) return null;

  const isHistorical =
    advisory.is_historical ||
    advisory.content_verification_status === 'verified_historical_reference' ||
    advisory.source_status === 'historical_reference' ||
    advisory.verification_status?.includes('historical') ||
    advisory.validity_period?.toLowerCase().includes('historical');

  const title = advisory.advisory_title || advisory.title || advisory.name || 'Agricultural Bulletin';
  const sourceName =
    advisory.source_name || advisory.issuing_authority || advisory.name || 'Official Agricultural Authority';
  const region = advisory.region || 'Maharashtra, India';
  const stage = advisory.applicable_stage || advisory.crop;
  const validity = advisory.validity_period || 'Seasonal Reference';
  const pubDate = advisory.publication_date || 'Unknown';
  const text = advisory.advisory_text || advisory.summary || advisory.purpose;
  const url = advisory.official_url || advisory.official_source_url || advisory.url;
  const sourceType = advisory.source_type || advisory.type;
  const sourceLabel = SOURCE_TYPE_LABELS[sourceType] || 'Official Source';
  const lastChecked = advisory.last_checked_at || advisory.last_verification_date;

  return (
    <div
      className="card advisory-card"
      style={{
        borderLeft: isHistorical ? '4px solid #ff9800' : '4px solid var(--primary-green)',
        padding: '1.25rem',
        marginBottom: '1rem',
        backgroundColor: '#ffffff',
      }}
    >
      {/* Header & Badges */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-start',
          flexWrap: 'wrap',
          gap: '0.5rem',
          marginBottom: '0.75rem',
        }}
      >
        <div style={{ flex: 1, minWidth: '260px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', marginBottom: '0.25rem' }}>
            <span
              className="badge"
              style={{
                fontSize: '0.7rem',
                backgroundColor: 'var(--bg-leaf)',
                color: 'var(--primary-dark)',
              }}
            >
              {sourceLabel}
            </span>
            {advisory.source_id && (
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                #{advisory.source_id}
              </span>
            )}
          </div>

          <h4
            style={{
              fontSize: '1.1rem',
              fontWeight: 700,
              color: 'var(--text-primary)',
              margin: '0.2rem 0 0.35rem 0',
            }}
          >
            {title}
          </h4>

          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              flexWrap: 'wrap',
              fontSize: '0.825rem',
              color: 'var(--text-secondary)',
            }}
          >
            <span style={{ display: 'flex', alignItems: 'center', gap: '0.25rem', fontWeight: 600 }}>
              <Building2 size={14} /> {sourceName}
            </span>
            <span>•</span>
            <span style={{ display: 'flex', alignItems: 'center', gap: '0.2rem' }}>
              <MapPin size={13} /> {region}
            </span>
            {stage && (
              <>
                <span>•</span>
                <span
                  className="badge"
                  style={{
                    backgroundColor: '#e8f5e9',
                    color: 'var(--primary-dark)',
                    fontSize: '0.725rem',
                  }}
                >
                  {stage}
                </span>
              </>
            )}
          </div>
        </div>

        {/* Verification Status Badge */}
        <div>
          {isHistorical ? (
            <span
              className="badge"
              style={{
                backgroundColor: '#fff3e0',
                color: '#e65100',
                border: '1px solid #ffe0b2',
                display: 'flex',
                alignItems: 'center',
                gap: '0.3rem',
                padding: '0.3rem 0.65rem',
              }}
            >
              <AlertTriangle size={13} /> Historical Reference Only
            </span>
          ) : (
            <span
              className="badge"
              style={{
                backgroundColor: 'var(--bg-leaf)',
                color: 'var(--primary-dark)',
                border: '1px solid #c8e6c9',
                display: 'flex',
                alignItems: 'center',
                gap: '0.3rem',
                padding: '0.3rem 0.65rem',
              }}
            >
              <ShieldCheck size={14} /> Verified Current Guidance
            </span>
          )}
        </div>
      </div>

      {/* Historical Warning Notice */}
      {isHistorical && (
        <div
          style={{
            fontSize: '0.825rem',
            backgroundColor: '#fff8e1',
            border: '1px solid #ffe082',
            padding: '0.65rem 0.85rem',
            borderRadius: 'var(--radius-sm)',
            color: '#8d4f00',
            marginBottom: '0.85rem',
            lineHeight: 1.45,
          }}
        >
          <strong>⚠️ Historical Baseline Record:</strong> This advisory was published for past seasons (
          {pubDate}). <strong>DO NOT</strong> apply chemical sprays or fertilizer doses from historical records as
          weather patterns, pest resistance, and label permissions vary. Verify with your local KVK agronomist.
        </div>
      )}

      {/* Advisory Text / Content */}
      {text && (
        <p
          style={{
            fontSize: '0.925rem',
            color: 'var(--text-primary)',
            lineHeight: 1.55,
            margin: '0.5rem 0',
          }}
        >
          {text}
        </p>
      )}

      {/* Field Action */}
      {advisory.field_action && (
        <div
          style={{
            marginTop: '0.5rem',
            padding: '0.5rem 0.75rem',
            backgroundColor: 'var(--bg-leaf)',
            border: '1px solid #c8e6c9',
            borderRadius: 'var(--radius-sm)',
            fontSize: '0.85rem',
            color: 'var(--primary-dark)',
          }}
        >
          <strong>Field Practice:</strong> {advisory.field_action}
        </div>
      )}

      {/* Precautions */}
      {advisory.precautions && (
        <div
          style={{
            marginTop: '0.5rem',
            padding: '0.5rem 0.75rem',
            backgroundColor: 'var(--bg-page)',
            borderRadius: 'var(--radius-sm)',
            fontSize: '0.85rem',
            border: '1px solid var(--border-color)',
          }}
        >
          <strong style={{ color: 'var(--earth-dark)' }}>Safety Precaution:</strong> {advisory.precautions}
        </div>
      )}

      {/* Footer & Source URL */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '0.5rem',
          marginTop: '1rem',
          paddingTop: '0.75rem',
          borderTop: '1px solid var(--border-color)',
          fontSize: '0.8rem',
          color: 'var(--text-muted)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
          <span style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
            <Calendar size={13} /> Published: <strong>{pubDate}</strong>
          </span>
          <span>•</span>
          <span style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
            <Clock size={13} /> Validity: <strong>{validity}</strong>
          </span>
          {lastChecked && (
            <>
              <span>•</span>
              <span>Checked: {lastChecked.slice(0, 10)}</span>
            </>
          )}
        </div>

        {url && url !== 'Unknown' && (
          <a
            href={url}
            target="_blank"
            rel="noopener noreferrer"
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.25rem',
              color: 'var(--primary-green)',
              fontWeight: 600,
              textDecoration: 'none',
            }}
          >
            <span>Visit Institutional Portal</span>
            <ExternalLink size={13} />
          </a>
        )}
      </div>
    </div>
  );
}
