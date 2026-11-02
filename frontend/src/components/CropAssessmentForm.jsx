import React, { useState } from 'react';
import { Sprout, AlertCircle, ArrowRight, Info } from 'lucide-react';

const PLANT_PARTS = [
  { value: 'older leaves', label: 'Older / Lower Leaves (खालची पाने)' },
  { value: 'newer leaves', label: 'Newer / Top Leaves (शेंड्याची पाने)' },
  { value: 'stems', label: 'Stems / Branches (फांद्या / खोड)' },
  { value: 'roots', label: 'Roots / Collar (मुळे / खोडाचा बुंधा)' },
  { value: 'flowers', label: 'Flowers / Squares (फुले / पाते)' },
  { value: 'pods or fruit', label: 'Pods / Green Bolls (शेंगा / बोंडे)' },
  { value: 'whole plant', label: 'Whole Plant (संपूर्ण झाड)' },
  { value: 'unknown', label: 'Not Sure / General (माहित नाही)' },
];

const SYMPTOM_OPTIONS = [
  { value: 'yellowing', label: 'Yellowing / Chlorosis (पाने पिवळी पडणे)' },
  { value: 'wilting', label: 'Wilting / Drooping (झाड कोमेgroupजणे / माना टाकणे)' },
  { value: 'spots', label: 'Spots / Lesions (पानांवर डाग / ठिपके)' },
  { value: 'holes', label: 'Holes / Chewed (पाने खाल्लेली / छिद्रे)' },
  { value: 'discoloration', label: 'Reddening / Browning (तांबडे / तपकिरी पडणे)' },
  { value: 'rot', label: 'Rot / Soft tissue (सड / कुजणे)' },
  { value: 'stunted growth', label: 'Stunted Growth (वाढ खुंटणे)' },
];

const DURATIONS = [
  { value: 'started today', label: 'Started Today (आजपासून)' },
  { value: 'a few days ago', label: 'A Few Days Ago (२-३ दिवसांपूर्वी)' },
  { value: 'more than a week ago', label: 'More than a Week Ago (आठवड्याहून अधिक)' },
  { value: 'unknown', label: 'Not Sure (माहित नाही)' },
];

const PATTERNS = [
  { value: 'whole field', label: 'Across Whole Field (संपूर्ण शेतात)' },
  { value: 'isolated patches', label: 'Isolated Patches (विशिष्ट तुकड्यांमध्ये / ठिकठिकाणी)' },
  { value: 'field edges', label: 'Field Edges / Bunds (बांधाच्या किंवा कडेने)' },
  { value: 'individual plants', label: 'Individual Plants (एकाकी झाडांवर)' },
  { value: 'unknown', label: 'Not Sure (माहित नाही)' },
];

const MOISTURES = [
  { value: 'dry', label: 'Dry (कोरडी माती)' },
  { value: 'normal', label: 'Normal / Moist (वाफसा / पुरेशी ओल)' },
  { value: 'waterlogged', label: 'Waterlogged (पाणथळ / पाणी साचलेले)' },
  { value: 'unknown', label: 'Not Sure (माहित नाही)' },
];

/**
 * Reusable Crop Assessment Form component collecting structured observations.
 */
export default function CropAssessmentForm({ onSubmit, loading }) {
  const [formData, setFormData] = useState({
    crop: 'soybean',
    growth_stage: 'Flowering',
    affected_part: 'older leaves',
    symptom_duration: 'a few days ago',
    field_pattern: 'isolated patches',
    soil_moisture: 'normal',
    recent_rainfall_or_irrigation: '',
    farmer_notes: '',
  });

  const [selectedSymptoms, setSelectedSymptoms] = useState(['yellowing']);
  const [customSymptom, setCustomSymptom] = useState('');
  const [validationError, setValidationError] = useState('');

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSymptomToggle = (symptomValue) => {
    setSelectedSymptoms((prev) =>
      prev.includes(symptomValue)
        ? prev.filter((s) => s !== symptomValue)
        : [...prev, symptomValue]
    );
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    setValidationError('');

    const symptomsList = [...selectedSymptoms];
    if (customSymptom.trim()) {
      symptomsList.push(customSymptom.trim());
    }

    if (symptomsList.length === 0) {
      setValidationError('Please select or describe at least one visible symptom.');
      return;
    }

    if (!formData.growth_stage.trim()) {
      setValidationError('Please provide the current growth stage.');
      return;
    }

    const payload = {
      crop: formData.crop,
      growth_stage: formData.growth_stage,
      symptoms: symptomsList,
      affected_part: formData.affected_part,
      affected_plant_parts: [formData.affected_part],
      symptom_duration: formData.symptom_duration,
      field_pattern: formData.field_pattern,
      soil_moisture: formData.soil_moisture,
      recent_rainfall_or_irrigation: formData.recent_rainfall_or_irrigation,
      recent_rainfall: formData.recent_rainfall_or_irrigation,
      farmer_notes: formData.farmer_notes,
    };

    onSubmit(payload);
  };

  return (
    <form onSubmit={handleSubmit} className="crop-assessment-form">
      {validationError && (
        <div className="alert alert-danger" style={{ marginBottom: '1rem' }} role="alert">
          <AlertCircle size={18} />
          <span>{validationError}</span>
        </div>
      )}

      {/* 1. Crop Selection */}
      <div className="form-group" style={{ marginBottom: '1.25rem' }}>
        <label className="form-label" style={{ fontWeight: 600 }}>
          1. Select Crop (पीक निवडा) *
        </label>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '0.75rem' }}>
          {[
            { id: 'soybean', label: 'Soybean (सोयाबीन)' },
            { id: 'cotton', label: 'Cotton (कापूस)' },
          ].map((item) => (
            <label
              key={item.id}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.6rem',
                padding: '0.85rem 1rem',
                borderRadius: 'var(--radius-md)',
                border: formData.crop === item.id ? '2px solid var(--primary-color)' : '1px solid var(--border-color)',
                backgroundColor: formData.crop === item.id ? 'var(--bg-leaf)' : '#ffffff',
                cursor: 'pointer',
                fontWeight: formData.crop === item.id ? 600 : 500,
              }}
            >
              <input
                type="radio"
                name="crop"
                value={item.id}
                checked={formData.crop === item.id}
                onChange={handleInputChange}
                style={{ accentColor: 'var(--primary-color)', width: '18px', height: '18px' }}
              />
              <span>{item.label}</span>
            </label>
          ))}
        </div>
      </div>

      {/* 2. Growth Stage */}
      <div className="form-group" style={{ marginBottom: '1.25rem' }}>
        <label className="form-label" style={{ fontWeight: 600 }}>
          2. Current Growth Stage (सध्याची वाढीची अवस्था) *
        </label>
        <select
          name="growth_stage"
          className="form-control"
          value={formData.growth_stage}
          onChange={handleInputChange}
          style={{ height: '46px', fontSize: '0.95rem' }}
        >
          {formData.crop === 'soybean' ? (
            <>
              <option value="Sowing and Emergence">Sowing / Emergence (उगवण अवस्था - 0-15 DAS)</option>
              <option value="Vegetative">Vegetative (शाकीय वाढ - 15-35 DAS)</option>
              <option value="Flowering">Flowering (फुलोरा अवस्था - 35-50 DAS)</option>
              <option value="Pod Filling">Pod Filling / Grain (शेंगा भरणे - 50-75 DAS)</option>
              <option value="Maturity">Maturity / Harvest (पक्वता / कापणी - 75+ DAS)</option>
            </>
          ) : (
            <>
              <option value="Seedling">Seedling / Early Vegetative (रोपावस्था - 0-25 DAS)</option>
              <option value="Squaring and Flowering">Squaring & Flowering (पाते व फुले - 45-65 DAS)</option>
              <option value="Boll Development">Boll Development (बोंड भरणे - 65-110 DAS)</option>
              <option value="Boll Bursting">Boll Bursting / Picking (बोंडे उमलणे / वेचणी - 110+ DAS)</option>
            </>
          )}
        </select>
      </div>

      {/* 3. Affected Plant Part */}
      <div className="form-group" style={{ marginBottom: '1.25rem' }}>
        <label className="form-label" style={{ fontWeight: 600 }}>
          3. Affected Plant Part (झाडाचा कोणता भाग बाधित आहे?) *
        </label>
        <select
          name="affected_part"
          className="form-control"
          value={formData.affected_part}
          onChange={handleInputChange}
          style={{ height: '46px', fontSize: '0.95rem' }}
        >
          {PLANT_PARTS.map((p) => (
            <option key={p.value} value={p.value}>
              {p.label}
            </option>
          ))}
        </select>
      </div>

      {/* 4. Visible Symptoms (Multi-select) */}
      <div className="form-group" style={{ marginBottom: '1.25rem' }}>
        <label className="form-label" style={{ fontWeight: 600 }}>
          4. Visible Symptoms (दिसणारी लक्षणे — एकापेक्षा जास्त निवडू शकता) *
        </label>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '0.5rem', marginBottom: '0.75rem' }}>
          {SYMPTOM_OPTIONS.map((s) => {
            const isChecked = selectedSymptoms.includes(s.value);
            return (
              <label
                key={s.value}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  padding: '0.6rem 0.75rem',
                  borderRadius: 'var(--radius-sm)',
                  border: isChecked ? '1px solid var(--primary-color)' : '1px solid var(--border-color)',
                  backgroundColor: isChecked ? 'var(--bg-leaf)' : '#ffffff',
                  cursor: 'pointer',
                  fontSize: '0.85rem',
                }}
              >
                <input
                  type="checkbox"
                  checked={isChecked}
                  onChange={() => handleSymptomToggle(s.value)}
                  style={{ accentColor: 'var(--primary-color)', width: '16px', height: '16px' }}
                />
                <span>{s.label}</span>
              </label>
            );
          })}
        </div>
        <input
          type="text"
          className="form-control"
          placeholder="Other specific symptom description (इतर लक्षणे)..."
          value={customSymptom}
          onChange={(e) => setCustomSymptom(e.target.value)}
          style={{ fontSize: '0.9rem' }}
        />
      </div>

      {/* Row: Duration & Field Distribution */}
      <div className="grid-2" style={{ marginBottom: '1.25rem' }}>
        <div className="form-group">
          <label className="form-label" style={{ fontWeight: 600 }}>
            5. Symptom Duration (लक्षणे कधीपासून दिसत आहेत?)
          </label>
          <select
            name="symptom_duration"
            className="form-control"
            value={formData.symptom_duration}
            onChange={handleInputChange}
          >
            {DURATIONS.map((d) => (
              <option key={d.value} value={d.value}>
                {d.label}
              </option>
            ))}
          </select>
        </div>

        <div className="form-group">
          <label className="form-label" style={{ fontWeight: 600 }}>
            6. Field Distribution (शेतात कुठे दिसत आहेत?)
          </label>
          <select
            name="field_pattern"
            className="form-control"
            value={formData.field_pattern}
            onChange={handleInputChange}
          >
            {PATTERNS.map((p) => (
              <option key={p.value} value={p.value}>
                {p.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Row: Soil Moisture & Recent Rainfall */}
      <div className="grid-2" style={{ marginBottom: '1.25rem' }}>
        <div className="form-group">
          <label className="form-label" style={{ fontWeight: 600 }}>
            7. Soil Moisture (मातीतील ओलावा)
          </label>
          <select
            name="soil_moisture"
            className="form-control"
            value={formData.soil_moisture}
            onChange={handleInputChange}
          >
            {MOISTURES.map((m) => (
              <option key={m.value} value={m.value}>
                {m.label}
              </option>
            ))}
          </select>
        </div>

        <div className="form-group">
          <label className="form-label" style={{ fontWeight: 600 }}>
            8. Recent Rain / Irrigation (अलीकडील पाऊस किंवा पाणी)
          </label>
          <input
            type="text"
            name="recent_rainfall_or_irrigation"
            className="form-control"
            placeholder="e.g. heavy rain 2 days ago, light irrigation (पाणी दिले)"
            value={formData.recent_rainfall_or_irrigation}
            onChange={handleInputChange}
          />
        </div>
      </div>

      {/* 9. Optional Notes */}
      <div className="form-group" style={{ marginBottom: '1.5rem' }}>
        <label className="form-label" style={{ fontWeight: 600 }}>
          9. Additional Farmer Notes (शेतकऱ्याची इतर नोंद - पर्यायी)
        </label>
        <textarea
          name="farmer_notes"
          className="form-control"
          rows={2}
          placeholder="Any other observations, soil type (काळी जमीन / मुरमाड), previous sprays, or nearby crop condition..."
          value={formData.farmer_notes}
          onChange={handleInputChange}
        />
      </div>

      <button
        type="submit"
        className="btn btn-primary"
        disabled={loading}
        style={{
          width: '100%',
          padding: '0.85rem',
          fontSize: '1.05rem',
          fontWeight: 600,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '0.5rem',
        }}
      >
        <Sprout size={20} />
        {loading ? 'Recording Field Observations...' : 'Generate Crop Assessment (तपासणी करा)'}
      </button>
    </form>
  );
}
