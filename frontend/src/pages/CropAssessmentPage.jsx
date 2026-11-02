import React, { useState } from 'react';
import {
  ClipboardList,
  CheckCircle2,
  AlertTriangle,
  Info,
  ShieldAlert,
  ArrowRight,
  Sprout,
  HelpCircle,
} from 'lucide-react';
import { assessCrop } from '../api';
import CropAssessmentForm from '../components/CropAssessmentForm';
import LoadingIndicator from '../components/LoadingIndicator';
import ErrorMessage from '../components/ErrorMessage';

export default function CropAssessmentPage({ onSaveAssessment }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState(null);

  const handleAssessmentSubmit = async (payload) => {
    setLoading(true);
    setError('');
    setResult(null);

    try {
      const response = await assessCrop(payload);
      setResult(response);
      if (onSaveAssessment) {
        onSaveAssessment(response);
      }
    } catch (err) {
      setError(err.message || 'Failed to complete symptom assessment.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container" style={{ maxWidth: '920px' }}>
      {/* Page Header */}
      <div style={{ marginBottom: '1.5rem' }}>
        <h2 style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--primary-dark)', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <ClipboardList size={28} /> Crop Health &amp; Symptom Assessment
        </h2>
        <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
          Record plant symptoms in a structured format. KrishiRakshak AI helps identify key diagnostic observations
          and possible explanations without prescribing unverified chemical doses.
        </p>
      </div>

      {/* Assessment Form Card */}
      <div className="card" style={{ marginBottom: '2rem' }}>
        <h3 className="card-title" style={{ marginBottom: '1.25rem' }}>
          <Sprout size={20} /> Field Observation Intake (शेत निरीक्षण नोंदणी)
        </h3>
        <CropAssessmentForm onSubmit={handleAssessmentSubmit} loading={loading} />
      </div>

      {loading && <LoadingIndicator message="Analyzing symptoms against ICAR agronomic guidance..." />}

      {error && <ErrorMessage message={error} style={{ marginBottom: '1.5rem' }} />}

      {/* Assessment Results Section */}
      {result && result.status === 'assessment_recorded' && (
        <div className="card" style={{ borderLeft: '4px solid var(--primary-color)', marginBottom: '2rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '0.5rem', marginBottom: '1rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <CheckCircle2 size={24} style={{ color: 'var(--primary-color)' }} />
              <h3 style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--primary-dark)', margin: 0 }}>
                Field Assessment Recorded
              </h3>
            </div>
            <span className="badge" style={{ backgroundColor: 'var(--bg-leaf)', color: 'var(--primary-dark)', fontSize: '0.85rem' }}>
              {result.crop} • {result.growth_stage}
            </span>
          </div>

          <div style={{ padding: '0.85rem', backgroundColor: 'var(--bg-page)', borderRadius: 'var(--radius-md)', marginBottom: '1.25rem', fontSize: '0.9rem', lineHeight: 1.5 }}>
            {result.message}
          </div>

          {/* Structured Observations Grid */}
          <div style={{ marginBottom: '1.5rem' }}>
            <h4 style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.03em' }}>
              Recorded Field Observations:
            </h4>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '0.75rem', fontSize: '0.85rem' }}>
              <div style={{ padding: '0.6rem 0.75rem', backgroundColor: '#ffffff', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-sm)' }}>
                <span style={{ color: 'var(--text-muted)', display: 'block', fontSize: '0.75rem' }}>AFFECTED PART</span>
                <strong>{result.affected_part}</strong>
              </div>
              <div style={{ padding: '0.6rem 0.75rem', backgroundColor: '#ffffff', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-sm)' }}>
                <span style={{ color: 'var(--text-muted)', display: 'block', fontSize: '0.75rem' }}>FIELD DISTRIBUTION</span>
                <strong>{result.field_pattern}</strong>
              </div>
              <div style={{ padding: '0.6rem 0.75rem', backgroundColor: '#ffffff', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-sm)' }}>
                <span style={{ color: 'var(--text-muted)', display: 'block', fontSize: '0.75rem' }}>SOIL MOISTURE</span>
                <strong>{result.soil_moisture}</strong>
              </div>
              <div style={{ padding: '0.6rem 0.75rem', backgroundColor: '#ffffff', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-sm)' }}>
                <span style={{ color: 'var(--text-muted)', display: 'block', fontSize: '0.75rem' }}>SYMPTOM DURATION</span>
                <strong>{result.symptom_duration || 'Not specified'}</strong>
              </div>
              {result.recent_rainfall && (
                <div style={{ padding: '0.6rem 0.75rem', backgroundColor: '#ffffff', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-sm)', gridColumn: 'span 2' }}>
                  <span style={{ color: 'var(--text-muted)', display: 'block', fontSize: '0.75rem' }}>RECENT RAINFALL / IRRIGATION</span>
                  <strong>{result.recent_rainfall}</strong>
                </div>
              )}
              {result.observations?.farmer_notes && (
                <div style={{ padding: '0.6rem 0.75rem', backgroundColor: '#ffffff', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-sm)', gridColumn: 'span 2' }}>
                  <span style={{ color: 'var(--text-muted)', display: 'block', fontSize: '0.75rem' }}>FARMER NOTES</span>
                  <strong>{result.observations.farmer_notes}</strong>
                </div>
              )}
            </div>
          </div>

          {/* Evidence-Based Possible Explanations */}
          {result.possible_explanations && result.possible_explanations.length > 0 && (
            <div style={{ marginBottom: '1.5rem', padding: '1rem', backgroundColor: '#f1f8e9', border: '1px solid #c5e1a5', borderRadius: 'var(--radius-md)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
                <Info size={18} style={{ color: 'var(--primary-dark)' }} />
                <h4 style={{ margin: 0, fontSize: '0.95rem', fontWeight: 700, color: 'var(--primary-dark)' }}>
                  Possible Explanations (For discussion with KVK / Agriculture Officer — NOT a confirmed diagnosis)
                </h4>
              </div>
              <p style={{ fontSize: '0.825rem', color: 'var(--text-secondary)', marginBottom: '0.75rem' }}>
                These are educational possibilities based on reported symptoms and agronomic factors in Maharashtra. They are not laboratory confirmations.
              </p>
              <ul style={{ margin: 0, paddingLeft: '1.25rem', display: 'flex', flexDirection: 'column', gap: '0.5rem', fontSize: '0.9rem' }}>
                {result.possible_explanations.map((exp, idx) => (
                  <li key={idx} style={{ lineHeight: 1.45 }}>{exp}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Missing Information Callout */}
          {result.missing_information && result.missing_information.length > 0 && (
            <div style={{ marginBottom: '1.5rem', padding: '1rem', backgroundColor: '#fff8e1', border: '1px solid #ffe082', borderRadius: 'var(--radius-md)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
                <HelpCircle size={18} style={{ color: '#b78103' }} />
                <h4 style={{ margin: 0, fontSize: '0.95rem', fontWeight: 700, color: '#8a6200' }}>
                  Information Needed for Accurate Diagnosis:
                </h4>
              </div>
              <ul style={{ margin: 0, paddingLeft: '1.25rem', display: 'flex', flexDirection: 'column', gap: '0.4rem', fontSize: '0.85rem' }}>
                {result.missing_information.map((item, idx) => (
                  <li key={idx}>{item}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Recommended Next Steps */}
          {result.recommended_next_steps && result.recommended_next_steps.length > 0 && (
            <div style={{ marginBottom: '1.5rem' }}>
              <h4 style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '0.5rem' }}>
                Recommended Actionable Next Steps:
              </h4>
              <ul style={{ margin: 0, paddingLeft: '1.25rem', display: 'flex', flexDirection: 'column', gap: '0.4rem', fontSize: '0.9rem' }}>
                {result.recommended_next_steps.map((step, idx) => (
                  <li key={idx} style={{ lineHeight: 1.45 }}>{step}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Chemical Guidance Notice */}
          <div style={{ padding: '0.75rem 1rem', backgroundColor: '#fafafa', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-sm)', marginBottom: '1rem', fontSize: '0.85rem' }}>
            <strong style={{ color: 'var(--text-primary)' }}>Chemical Treatments:</strong> No pesticide or chemical dose is prescribed. Do not spray chemicals without confirmed diagnosis from an agricultural extension officer.
          </div>

          {/* Safety Note Alert */}
          {result.safety_note && (
            <div className="alert alert-warning" style={{ fontSize: '0.85rem' }}>
              <ShieldAlert size={18} style={{ flexShrink: 0 }} />
              <span>{result.safety_note}</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
