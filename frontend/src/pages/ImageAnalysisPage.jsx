import React, { useState } from 'react';
import {
  Camera,
  CheckCircle2,
  ShieldAlert,
  AlertTriangle,
  Sparkles,
  Info,
  Eye,
  CheckSquare,
  HelpCircle,
  FileText,
  AlertCircle,
} from 'lucide-react';
import { analyzeCropImage } from '../api';
import ImageUpload from '../components/ImageUpload';
import LoadingIndicator from '../components/LoadingIndicator';
import ErrorMessage from '../components/ErrorMessage';

const CROPS = [
  { value: '', label: '-- Not specified / Crop in photo --' },
  { value: 'soybean', label: 'Soybean (सोयाबीन)' },
  { value: 'cotton', label: 'Cotton (कापूस)' },
];

const GROWTH_STAGES = [
  { value: '', label: '-- Select growth stage (optional) --' },
  { value: 'Seedling / Vegetative', label: 'Seedling / Vegetative (रोपावस्था / शाकीय वाढ)' },
  { value: 'Flowering', label: 'Flowering (फुलोरा अवस्था)' },
  { value: 'Pod / Boll formation', label: 'Pod / Boll formation (शेंगा / बोंड निर्मिती)' },
  { value: 'Maturity / Pre-harvest', label: 'Maturity / Pre-harvest (पक्वता अवस्था)' },
  { value: 'Other / Unknown', label: 'Other / Unknown' },
];

export default function ImageAnalysisPage() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [crop, setCrop] = useState('');
  const [growthStage, setGrowthStage] = useState('');
  const [notes, setNotes] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState(null);

  const handleFileSelect = (file) => {
    setSelectedFile(file);
    setError('');
    setResult(null);
  };

  const handleClear = () => {
    setSelectedFile(null);
    setCrop('');
    setGrowthStage('');
    setNotes('');
    setResult(null);
    setError('');
  };

  const handleAnalyze = async () => {
    if (!selectedFile) return;

    setLoading(true);
    setError('');
    setResult(null);

    try {
      const response = await analyzeCropImage(
        selectedFile,
        crop || null,
        growthStage || null,
        notes || null
      );
      setResult(response);
    } catch (err) {
      setError(err.message || 'Image upload or analysis failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container" style={{ maxWidth: '920px' }}>
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
          <Camera size={28} /> Crop Photo Analysis (छायाचित्र तपासणी)
        </h2>
        <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
          Upload clear photographs of crop leaves, stems, or pods/bolls for Soybean and Cotton.
          The assistant provides objective visual observations and highlights uncertainties.
          <strong> Automated scans never replace physical field diagnostics or prescribe chemical dosages.</strong>
        </p>
      </div>

      {/* Main Upload and Context Form */}
      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <div style={{ marginBottom: '1.25rem' }}>
          <h3 className="card-title" style={{ fontSize: '1.05rem', marginBottom: '0.5rem' }}>
            <Camera size={20} /> 1. Upload Crop Photograph
          </h3>
          <ImageUpload
            onFileSelect={handleFileSelect}
            onClear={handleClear}
            selectedFile={selectedFile}
            disabled={loading}
          />
        </div>

        {/* Crop Context Details */}
        <div
          style={{
            borderTop: '1px solid var(--border-color)',
            paddingTop: '1.25rem',
            marginTop: '1.25rem',
          }}
        >
          <h3 className="card-title" style={{ fontSize: '1.05rem', marginBottom: '0.75rem' }}>
            <FileText size={20} /> 2. Crop Context (पिकाची माहिती - पर्यायी पण शिफारसीत)
          </h3>
          <div className="grid-2" style={{ marginBottom: '1rem' }}>
            <div className="form-group">
              <label htmlFor="crop-select" className="form-label">
                Crop Name (पीक निवडा)
              </label>
              <select
                id="crop-select"
                className="form-control"
                value={crop}
                onChange={(e) => setCrop(e.target.value)}
                disabled={loading}
              >
                {CROPS.map((c) => (
                  <option key={c.value} value={c.value}>
                    {c.label}
                  </option>
                ))}
              </select>
              <p className="form-hint">Currently supporting Soybean and Cotton in Maharashtra.</p>
            </div>

            <div className="form-group">
              <label htmlFor="stage-select" className="form-label">
                Growth Stage (वाढीची अवस्था)
              </label>
              <select
                id="stage-select"
                className="form-control"
                value={growthStage}
                onChange={(e) => setGrowthStage(e.target.value)}
                disabled={loading}
              >
                {GROWTH_STAGES.map((s) => (
                  <option key={s.value} value={s.value}>
                    {s.label}
                  </option>
                ))}
              </select>
              <p className="form-hint">Stage helps identify whether symptoms are age-related.</p>
            </div>
          </div>

          <div className="form-group" style={{ marginBottom: '1.25rem' }}>
            <label htmlFor="notes-input" className="form-label">
              Farmer Observations / Notes (शेतकऱ्याची निरीक्षणे)
            </label>
            <textarea
              id="notes-input"
              className="form-control"
              rows={2}
              placeholder="e.g. Yellow spots noticed after 2 days of continuous rain, mostly on lower leaves..."
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              disabled={loading}
            />
            <p className="form-hint">
              Mention recent rainfall, irrigation, or pattern in the field if known.
            </p>
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem' }}>
            <button
              type="button"
              onClick={handleClear}
              className="btn btn-secondary"
              disabled={loading || (!selectedFile && !crop && !growthStage && !notes)}
            >
              Reset
            </button>
            <button
              type="button"
              onClick={handleAnalyze}
              className="btn btn-primary"
              disabled={loading || !selectedFile}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.4rem',
                fontWeight: 600,
                padding: '0.65rem 1.25rem',
              }}
            >
              <Sparkles size={18} />
              <span>{loading ? 'Analyzing Photograph...' : 'Analyze Photo (तपासणी करा)'}</span>
            </button>
          </div>
        </div>
      </div>

      {loading && (
        <LoadingIndicator message="Validating image bytes and coordinating objective visual observations..." />
      )}

      {error && <ErrorMessage message={error} style={{ marginBottom: '1.5rem' }} />}

      {/* Result Display: Vision Unavailable State */}
      {result && result.status === 'vision_unavailable' && (
        <div className="card" style={{ borderLeft: '4px solid #ff9800', marginBottom: '1.5rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem' }}>
            <AlertTriangle size={22} style={{ color: '#e65100' }} />
            <h3 style={{ margin: 0, fontSize: '1.15rem', fontWeight: 700, color: '#e65100' }}>
              Vision Service Notice (दृष्टी सेवा अनुपलब्ध)
            </h3>
          </div>
          <p
            style={{
              fontSize: '0.925rem',
              color: 'var(--text-primary)',
              lineHeight: 1.5,
              marginBottom: '0.75rem',
            }}
          >
            {result.message}
          </p>
          <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '1rem' }}>
            Validated file: <strong>{result.file_name}</strong> (
            {(result.file_size_bytes / 1024).toFixed(1)} KB, {result.content_type})
          </div>

          {result.safety_note && (
            <div className="alert alert-warning" style={{ fontSize: '0.85rem', margin: 0 }}>
              <ShieldAlert size={18} style={{ flexShrink: 0 }} />
              <span>{result.safety_note}</span>
            </div>
          )}
        </div>
      )}

      {/* Result Display: Completed Analysis State */}
      {result && result.status === 'analysis_completed' && (
        <div className="card" style={{ borderLeft: '4px solid var(--primary-green)', marginBottom: '1.5rem' }}>
          {/* Header */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              flexWrap: 'wrap',
              gap: '0.5rem',
              marginBottom: '1rem',
              paddingBottom: '0.75rem',
              borderBottom: '1px solid var(--border-color)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <CheckCircle2 size={24} style={{ color: 'var(--primary-green)' }} />
              <h3 style={{ margin: 0, fontSize: '1.25rem', fontWeight: 700, color: 'var(--primary-dark)' }}>
                Visual Observations Completed (दृश्य निरीक्षणे)
              </h3>
            </div>
            <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
              {result.crop && (
                <span className="badge badge-green">
                  Crop: {result.crop}
                </span>
              )}
              <span className="badge badge-gray">
                {result.file_name} • {(result.file_size_bytes / 1024).toFixed(1)} KB
              </span>
            </div>
          </div>

          {/* Narrative / Overview */}
          {result.narrative && (
            <div
              style={{
                padding: '0.875rem 1rem',
                backgroundColor: 'var(--bg-leaf)',
                borderRadius: 'var(--radius-md)',
                marginBottom: '1.25rem',
                fontSize: '0.95rem',
                lineHeight: 1.5,
                color: 'var(--primary-dark)',
              }}
            >
              <strong>Summary Overview:</strong> {result.narrative}
            </div>
          )}

          {/* Section 1 & 2: Visible Parts & Symptoms */}
          <div className="grid-2" style={{ marginBottom: '1.25rem' }}>
            {/* Visible Plant Parts */}
            <div
              style={{
                backgroundColor: 'var(--bg-page)',
                padding: '1rem',
                borderRadius: 'var(--radius-md)',
                border: '1px solid var(--border-color)',
              }}
            >
              <h4
                style={{
                  fontSize: '0.95rem',
                  fontWeight: 600,
                  color: 'var(--primary-dark)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.4rem',
                  marginBottom: '0.65rem',
                }}
              >
                <Eye size={18} /> Visible Plant Parts (दिसणारे भाग)
              </h4>
              {result.visible_plant_parts && result.visible_plant_parts.length > 0 ? (
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem' }}>
                  {result.visible_plant_parts.map((part, idx) => (
                    <span key={idx} className="badge badge-green">
                      {part}
                    </span>
                  ))}
                </div>
              ) : (
                <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', margin: 0 }}>
                  No specific plant parts isolated.
                </p>
              )}
            </div>

            {/* Observable Visual Symptoms */}
            <div
              style={{
                backgroundColor: 'var(--bg-page)',
                padding: '1rem',
                borderRadius: 'var(--radius-md)',
                border: '1px solid var(--border-color)',
              }}
            >
              <h4
                style={{
                  fontSize: '0.95rem',
                  fontWeight: 600,
                  color: 'var(--earth-dark)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.4rem',
                  marginBottom: '0.65rem',
                }}
              >
                <CheckSquare size={18} /> Observable Symptoms (दृश्य लक्षणे)
              </h4>
              {result.observable_visual_symptoms && result.observable_visual_symptoms.length > 0 ? (
                <ul style={{ paddingLeft: '1.2rem', margin: 0, fontSize: '0.875rem' }}>
                  {result.observable_visual_symptoms.map((sym, idx) => (
                    <li key={idx} style={{ marginBottom: '0.25rem' }}>
                      {sym}
                    </li>
                  ))}
                </ul>
              ) : (
                <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', margin: 0 }}>
                  No specific visual abnormalities detected.
                </p>
              )}
            </div>
          </div>

          {/* Section 3: Possible Explanations (Explicitly non-confirmed) */}
          <div
            style={{
              backgroundColor: '#fff9e6',
              border: '1px solid #ffe082',
              borderRadius: 'var(--radius-md)',
              padding: '1rem',
              marginBottom: '1.25rem',
            }}
          >
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                flexWrap: 'wrap',
                gap: '0.5rem',
                marginBottom: '0.65rem',
              }}
            >
              <h4
                style={{
                  fontSize: '0.95rem',
                  fontWeight: 700,
                  color: '#b78103',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.4rem',
                  margin: 0,
                }}
              >
                <HelpCircle size={18} /> Possible Explanations (संभाव्य कारणे - निश्चित निदान नव्हे)
              </h4>
              <span className="badge badge-amber" style={{ fontSize: '0.7rem' }}>
                Non-Confirmed Hypotheses Only
              </span>
            </div>
            {result.possible_explanations && result.possible_explanations.length > 0 ? (
              <ul style={{ paddingLeft: '1.2rem', margin: 0, fontSize: '0.875rem', color: '#5d4037' }}>
                {result.possible_explanations.map((exp, idx) => (
                  <li key={idx} style={{ marginBottom: '0.35rem' }}>
                    {exp}
                  </li>
                ))}
              </ul>
            ) : (
              <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', margin: 0 }}>
                Visual cues do not clearly match a known pattern. Field testing is recommended.
              </p>
            )}
          </div>

          {/* Section 4 & 5: Image Quality Limitations & Additional Observations Needed */}
          <div className="grid-2" style={{ marginBottom: '1.25rem' }}>
            {/* Image Quality Limitations */}
            <div
              style={{
                backgroundColor: 'var(--bg-page)',
                padding: '1rem',
                borderRadius: 'var(--radius-md)',
                border: '1px solid var(--border-color)',
              }}
            >
              <h4
                style={{
                  fontSize: '0.95rem',
                  fontWeight: 600,
                  color: 'var(--text-secondary)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.4rem',
                  marginBottom: '0.65rem',
                }}
              >
                <Info size={18} /> Image Quality Limitations (मर्यादा)
              </h4>
              {result.image_quality_limitations && result.image_quality_limitations.length > 0 ? (
                <ul style={{ paddingLeft: '1.2rem', margin: 0, fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                  {result.image_quality_limitations.map((lim, idx) => (
                    <li key={idx} style={{ marginBottom: '0.25rem' }}>
                      {lim}
                    </li>
                  ))}
                </ul>
              ) : (
                <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', margin: 0 }}>
                  Standard image clarity.
                </p>
              )}
            </div>

            {/* Additional Observations Needed */}
            <div
              style={{
                backgroundColor: 'var(--bg-page)',
                padding: '1rem',
                borderRadius: 'var(--radius-md)',
                border: '1px solid var(--border-color)',
              }}
            >
              <h4
                style={{
                  fontSize: '0.95rem',
                  fontWeight: 600,
                  color: 'var(--primary-dark)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.4rem',
                  marginBottom: '0.65rem',
                }}
              >
                <CheckSquare size={18} /> Additional Field Checks (शेत पाहणी)
              </h4>
              {result.additional_observations_needed && result.additional_observations_needed.length > 0 ? (
                <ul style={{ paddingLeft: '1.2rem', margin: 0, fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                  {result.additional_observations_needed.map((obs, idx) => (
                    <li key={idx} style={{ marginBottom: '0.25rem' }}>
                      {obs}
                    </li>
                  ))}
                </ul>
              ) : (
                <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', margin: 0 }}>
                  Compare with surrounding healthy plants.
                </p>
              )}
            </div>
          </div>

          {/* Section 6: Recommended Safe Next Steps */}
          {result.recommended_safe_next_steps && result.recommended_safe_next_steps.length > 0 && (
            <div
              style={{
                backgroundColor: 'var(--bg-page)',
                padding: '1rem',
                borderRadius: 'var(--radius-md)',
                border: '1px solid var(--border-color)',
                marginBottom: '1.25rem',
              }}
            >
              <h4
                style={{
                  fontSize: '0.95rem',
                  fontWeight: 600,
                  color: 'var(--primary-dark)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.4rem',
                  marginBottom: '0.65rem',
                }}
              >
                <ShieldAlert size={18} /> Recommended Safe Next Steps (सुरक्षित उपाययोजना)
              </h4>
              <ul style={{ paddingLeft: '1.2rem', margin: 0, fontSize: '0.875rem' }}>
                {result.recommended_safe_next_steps.map((step, idx) => (
                  <li key={idx} style={{ marginBottom: '0.3rem' }}>
                    {step}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* In-Person Professional Assessment Advisable Alert */}
          {result.professional_assessment_advisable && (
            <div
              className="alert alert-info"
              style={{
                fontSize: '0.875rem',
                marginBottom: '1rem',
                display: 'flex',
                alignItems: 'center',
                gap: '0.6rem',
              }}
            >
              <AlertCircle size={20} style={{ flexShrink: 0 }} />
              <div>
                <strong>Professional In-Person Assessment Recommended:</strong> Take fresh, representative leaf and stem
                specimens in a sealed bag to your nearest Taluka Agriculture Officer (तालुका कृषी अधिकारी) or Krishi
                Vigyan Kendra (KVK) agronomy diagnostic lab.
              </div>
            </div>
          )}

          {/* Uncertainty Note */}
          {result.uncertainty_note && (
            <div
              className="alert alert-warning"
              style={{ fontSize: '0.85rem', marginBottom: '0.75rem', lineHeight: 1.4 }}
            >
              <AlertTriangle size={18} style={{ flexShrink: 0 }} />
              <span>{result.uncertainty_note}</span>
            </div>
          )}

          {/* Safety Note */}
          {result.safety_note && (
            <div
              className="alert alert-danger"
              style={{ fontSize: '0.85rem', margin: 0, lineHeight: 1.4 }}
            >
              <ShieldAlert size={18} style={{ flexShrink: 0 }} />
              <span>
                <strong>Safety Invariant:</strong> {result.safety_note}
              </span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
